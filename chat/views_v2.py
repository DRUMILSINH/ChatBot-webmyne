import json
import re
from datetime import datetime, timezone
from typing import Any

from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from chatbot.vector_store import get_vector_store
from chat.backpressure import high_load, stream_limiter
from chat.models import ChatMessage, ChatSession, MessageFeedback
from chat.observability import log_audit
from chat.rbac import role_required
from chat.security import sanitize_debug_payload
from chat.services_v2 import run_secure_chat_query


def _json_body(request) -> dict[str, Any]:
    if not request.body:
        return {}
    return json.loads(request.body.decode("utf-8"))


def _session_key(request) -> str:
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _can_access_chat_session(request, chat_session: ChatSession) -> bool:
    if request.user.is_authenticated and chat_session.created_by_id:
        return request.user.is_superuser or request.user.id == chat_session.created_by_id
    return chat_session.session_key == _session_key(request)


def _serialize_session(chat_session: ChatSession) -> dict[str, Any]:
    return {
        "id": str(chat_session.id),
        "title": chat_session.title,
        "vector_id": chat_session.vector_id,
        "is_archived": chat_session.is_archived,
        "created_at": chat_session.created_at.isoformat(),
        "updated_at": chat_session.updated_at.isoformat(),
    }


def _serialize_message(message: ChatMessage) -> dict[str, Any]:
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "sources": message.sources,
        "confidence": message.confidence,
        "token_usage": {
            "prompt_tokens": message.prompt_tokens,
            "completion_tokens": message.completion_tokens,
            "total_tokens": message.total_tokens,
        },
        "model_info": {"model": message.model_name},
        "latency_ms": message.latency_ms,
        "created_at": message.created_at.isoformat(),
        "trace_id": message.trace_id,
    }


def _safe_title_from_query(query: str) -> str:
    cleaned = re.sub(r"\s+", " ", (query or "").strip())
    if not cleaned:
        return "New Chat"
    return cleaned[:80]


def _extract_source_url(metadata: dict[str, Any]) -> str:
    raw_url = metadata.get("url") or metadata.get("source") or ""
    return str(raw_url).strip()


def _retrieved_chunks_from_result(result: dict[str, Any]) -> list[dict[str, Any]]:
    debug_payload = result.get("debug") or {}
    chunks = debug_payload.get("retrieved_chunks") or debug_payload.get("retrieved_documents")
    if not chunks:
        chunks = result.get("sources") or []
    return chunks if isinstance(chunks, list) else []


def _telemetry_response_fields(result: dict[str, Any]) -> dict[str, Any]:
    token_usage = result.get("token_usage") or {}
    latency_ms = result.get("latency_ms") or {}
    retrieved_chunks = _retrieved_chunks_from_result(result)
    def to_int(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    return {
        "prompt_tokens": to_int(token_usage.get("prompt_tokens", 0)),
        "completion_tokens": to_int(token_usage.get("completion_tokens", 0)),
        "total_tokens": to_int(token_usage.get("total_tokens", 0)),
        "latency_ms": latency_ms,
        "retrieved_chunks": retrieved_chunks,
    }


@ensure_csrf_cookie
@require_http_methods(["GET"])
def csrf_bootstrap(request):
    return JsonResponse({"status": "ok"})


@role_required("chat_user", "chat_admin")
@require_http_methods(["GET"])
def knowledge_base_stats(request):
    vector_id = (request.GET.get("vector_id") or "").strip()
    if not vector_id:
        return JsonResponse({"error": "Missing vector_id query parameter."}, status=400)

    try:
        vector_store = get_vector_store(vector_id)
        total_vectors = int(vector_store._collection.count())
        payload = vector_store.get(include=["metadatas"])
    except FileNotFoundError:
        return JsonResponse(
            {"error": f"Vector collection '{vector_id}' was not found."},
            status=404,
        )
    except Exception as exc:
        return JsonResponse({"error": f"Failed to load collection metadata: {exc}"}, status=500)

    metadatas = payload.get("metadatas") or []
    if not isinstance(metadatas, list):
        metadatas = []

    url_counts: dict[str, int] = {}
    chunk_ids: set[str] = set()
    chunks_with_source_url = 0

    for item in metadatas:
        metadata = item if isinstance(item, dict) else {}
        chunk_id = str(metadata.get("chunk_id") or "").strip()
        if chunk_id:
            chunk_ids.add(chunk_id)

        source_url = _extract_source_url(metadata)
        if not source_url:
            continue

        chunks_with_source_url += 1
        url_counts[source_url] = url_counts.get(source_url, 0) + 1

    top_sources = [
        {"url": url, "chunk_count": count}
        for url, count in sorted(url_counts.items(), key=lambda item: (-item[1], item[0]))[:20]
    ]
    sample_urls = sorted(url_counts.keys())[:20]

    total_chunks = total_vectors if total_vectors > 0 else len(metadatas)
    chunks_without_source_url = max(0, total_chunks - chunks_with_source_url)

    response = {
        "vector_id": vector_id,
        "total_vectors": total_vectors,
        "total_chunks": total_chunks,
        "metadata_records": len(metadatas),
        "unique_chunk_ids": len(chunk_ids),
        "unique_urls": len(url_counts),
        "chunks_with_source_url": chunks_with_source_url,
        "chunks_without_source_url": chunks_without_source_url,
        "top_sources": top_sources,
        "sample_urls": sample_urls,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return JsonResponse(response, status=200)


@role_required("chat_user", "chat_admin")
@require_http_methods(["POST", "GET"])
def chats(request):
    if request.method == "POST":
        try:
            data = _json_body(request)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON body."}, status=400)

        vector_id = (data.get("vector_id") or "").strip()
        title = (data.get("title") or "New Chat").strip()[:200]
        if not vector_id:
            return JsonResponse({"error": "Missing vector_id."}, status=400)

        chat_session = ChatSession.objects.create(
            title=title or "New Chat",
            vector_id=vector_id,
            session_key=_session_key(request),
            created_by=request.user if request.user.is_authenticated else None,
            metadata=data.get("metadata") or {},
        )
        log_audit(
            trace_id=getattr(request, "trace_id", ""),
            actor=request.user,
            event_type="chat_session_created",
            session_key=chat_session.session_key,
            metadata={"chat_session_id": str(chat_session.id), "vector_id": vector_id},
        )
        return JsonResponse({"chat": _serialize_session(chat_session)}, status=201)

    qs = ChatSession.objects.filter(is_archived=False)
    if request.user.is_authenticated:
        qs = qs.filter(created_by=request.user)
    else:
        qs = qs.filter(session_key=_session_key(request))
    sessions = [_serialize_session(item) for item in qs.order_by("-updated_at")[:100]]
    return JsonResponse({"items": sessions}, status=200)


@role_required("chat_user", "chat_admin")
@require_http_methods(["GET", "POST"])
def chat_messages(request, chat_id):
    try:
        chat_session = ChatSession.objects.get(id=chat_id)
    except ChatSession.DoesNotExist:
        return JsonResponse({"error": "Chat session not found."}, status=404)

    if not _can_access_chat_session(request, chat_session):
        return JsonResponse({"error": "Forbidden."}, status=403)

    if request.method == "GET":
        messages = chat_session.messages.order_by("created_at")
        return JsonResponse({"items": [_serialize_message(msg) for msg in messages]}, status=200)

    try:
        data = _json_body(request)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    query = (data.get("query") or "").strip()
    if not query:
        return JsonResponse({"error": "Missing query."}, status=400)

    vector_id = (data.get("vector_id") or chat_session.vector_id).strip()
    trace_id = getattr(request, "trace_id", "")
    session_key = _session_key(request)

    user_msg = ChatMessage.objects.create(
        chat_session=chat_session,
        role=ChatMessage.ROLE_USER,
        content=query,
        trace_id=trace_id,
    )

    result = run_secure_chat_query(
        query=query,
        vector_id=vector_id,
        user=request.user,
        trace_id=trace_id,
        session_key=session_key,
        load_high=high_load(),
    )

    assistant_msg = ChatMessage.objects.create(
        chat_session=chat_session,
        role=ChatMessage.ROLE_ASSISTANT,
        content=result["answer"],
        sources=result["sources"],
        debug_info=result["debug"],
        confidence=result["confidence"],
        model_name=result["model_info"]["model"],
        prompt_tokens=result["token_usage"]["prompt_tokens"],
        completion_tokens=result["token_usage"]["completion_tokens"],
        total_tokens=result["token_usage"]["total_tokens"],
        latency_ms=result["latency_ms"]["total"],
        trace_id=trace_id,
    )

    if chat_session.title == "New Chat":
        chat_session.title = _safe_title_from_query(query)
        chat_session.save(update_fields=["title", "updated_at"])

    response = {
        "chat_session_id": str(chat_session.id),
        "user_message_id": user_msg.id,
        "assistant_message_id": assistant_msg.id,
        "answer": result["answer"],
        "sources": result["sources"],
        "confidence": result["confidence"],
        "token_usage": result["token_usage"],
        "model_info": result["model_info"],
        **_telemetry_response_fields(result),
    }
    return JsonResponse(response, status=200)


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@role_required("chat_user", "chat_admin")
@require_http_methods(["POST"])
def chat_stream(request):
    if getattr(settings, "SSE_REQUIRE_ASGI", True) and "wsgi.version" in request.META:
        return JsonResponse(
            {"error": "Streaming requires ASGI runtime. Run the app with Uvicorn/Daphne for SSE."},
            status=503,
        )

    if not stream_limiter.has_capacity():
        return JsonResponse(
            {"error": "Streaming capacity reached. Please retry shortly."},
            status=429,
        )

    try:
        data = _json_body(request)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    query = (data.get("query") or "").strip()
    vector_id = (data.get("vector_id") or "").strip()
    chat_session_id = data.get("chat_session_id")
    trace_id = getattr(request, "trace_id", "")
    session_key = _session_key(request)

    if not query or not vector_id:
        return JsonResponse({"error": "query and vector_id are required."}, status=400)

    if chat_session_id:
        try:
            chat_session = ChatSession.objects.get(id=chat_session_id)
        except ChatSession.DoesNotExist:
            return JsonResponse({"error": "Chat session not found."}, status=404)
        if not _can_access_chat_session(request, chat_session):
            return JsonResponse({"error": "Forbidden."}, status=403)
    else:
        chat_session = ChatSession.objects.create(
            title=_safe_title_from_query(query),
            vector_id=vector_id,
            session_key=session_key,
            created_by=request.user if request.user.is_authenticated else None,
        )

    user_msg = ChatMessage.objects.create(
        chat_session=chat_session,
        role=ChatMessage.ROLE_USER,
        content=query,
        trace_id=trace_id,
    )
    result = run_secure_chat_query(
        query=query,
        vector_id=vector_id,
        user=request.user,
        trace_id=trace_id,
        session_key=session_key,
        load_high=high_load(),
    )

    assistant_msg = ChatMessage.objects.create(
        chat_session=chat_session,
        role=ChatMessage.ROLE_ASSISTANT,
        content=result["answer"],
        sources=result["sources"],
        debug_info=result["debug"],
        confidence=result["confidence"],
        model_name=result["model_info"]["model"],
        prompt_tokens=result["token_usage"]["prompt_tokens"],
        completion_tokens=result["token_usage"]["completion_tokens"],
        total_tokens=result["token_usage"]["total_tokens"],
        latency_ms=result["latency_ms"]["total"],
        trace_id=trace_id,
    )

    tokens = re.findall(r"\S+\s*", result["answer"])

    def event_stream_sync():
        with stream_limiter.acquire():
            yield _sse(
                "start",
                {
                    "trace_id": trace_id,
                    "chat_session_id": str(chat_session.id),
                    "user_message_id": user_msg.id,
                },
            )
            for token in tokens:
                yield _sse("token", {"token": token})
            yield _sse(
                "done",
                {
                    "assistant_message_id": assistant_msg.id,
                    "answer": result["answer"],
                    "sources": result["sources"],
                    "confidence": result["confidence"],
                    "token_usage": result["token_usage"],
                    "model_info": result["model_info"],
                    **_telemetry_response_fields(result),
                },
            )

    async def event_stream_async():
        with stream_limiter.acquire():
            yield _sse(
                "start",
                {
                    "trace_id": trace_id,
                    "chat_session_id": str(chat_session.id),
                    "user_message_id": user_msg.id,
                },
            )
            for token in tokens:
                yield _sse("token", {"token": token})
            yield _sse(
                "done",
                {
                    "assistant_message_id": assistant_msg.id,
                    "answer": result["answer"],
                    "sources": result["sources"],
                    "confidence": result["confidence"],
                    "token_usage": result["token_usage"],
                    "model_info": result["model_info"],
                    **_telemetry_response_fields(result),
                },
            )

    stream = event_stream_sync() if "wsgi.version" in request.META else event_stream_async()
    response = StreamingHttpResponse(stream, content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    response["Connection"] = "keep-alive"
    return response


@role_required("chat_analyst", "chat_admin", force=True)
@require_http_methods(["GET"])
def chat_debug(request, message_id: int):
    try:
        message = ChatMessage.objects.select_related("chat_session").get(id=message_id)
    except ChatMessage.DoesNotExist:
        return JsonResponse({"error": "Message not found."}, status=404)

    if not _can_access_chat_session(request, message.chat_session) and not request.user.is_superuser:
        return JsonResponse({"error": "Forbidden."}, status=403)

    debug_payload = message.debug_info or {}
    debug_payload.setdefault("sources", message.sources)
    debug_payload.setdefault(
        "token_usage",
        {
            "prompt_tokens": message.prompt_tokens,
            "completion_tokens": message.completion_tokens,
            "total_tokens": message.total_tokens,
        },
    )
    debug_payload.setdefault("prompt_tokens", message.prompt_tokens)
    debug_payload.setdefault("completion_tokens", message.completion_tokens)
    debug_payload.setdefault("total_tokens", message.total_tokens)
    debug_payload.setdefault("latency_ms", {"total": message.latency_ms})
    debug_payload.setdefault("retrieved_chunks", debug_payload.get("retrieved_documents") or message.sources)
    debug_payload.setdefault("retrieved_documents", debug_payload.get("retrieved_chunks") or message.sources)
    debug_payload.setdefault("model_info", {"model": message.model_name})
    debug_payload.setdefault("confidence", message.confidence)
    debug_payload.setdefault("trace_id", message.trace_id)
    debug_payload = sanitize_debug_payload(debug_payload)

    return JsonResponse({"message_id": message.id, "debug": debug_payload}, status=200)


@role_required("chat_user", "chat_admin")
@require_http_methods(["POST"])
def chat_feedback(request):
    try:
        data = _json_body(request)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    message_id = data.get("message_id")
    rating = data.get("rating")
    correction = (data.get("correction") or "").strip()

    if message_id is None or rating not in (1, -1):
        return JsonResponse({"error": "message_id and rating (1 or -1) are required."}, status=400)

    try:
        message = ChatMessage.objects.select_related("chat_session").get(id=message_id)
    except ChatMessage.DoesNotExist:
        return JsonResponse({"error": "Message not found."}, status=404)

    if not _can_access_chat_session(request, message.chat_session):
        return JsonResponse({"error": "Forbidden."}, status=403)

    feedback = MessageFeedback.objects.create(
        message=message,
        created_by=request.user if request.user.is_authenticated else None,
        rating=rating,
        correction=correction,
        metadata={"trace_id": getattr(request, "trace_id", "")},
    )
    return JsonResponse({"feedback_id": feedback.id, "status": "saved"}, status=201)
