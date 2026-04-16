import hashlib
import json
import copy
import re
import threading
import time
from typing import Any

from django.conf import settings
from django.core.cache import cache

from chatbot.prompt import system_prompt
from chatbot.retrieval import compress_context, confidence_from_docs, hybrid_retrieve
from chat.observability import log_audit, log_event
from chat.security import (
    safe_block_message,
    sanitize_output,
    sanitize_text,
    violates_input_policy,
    violates_output_policy,
)

try:
    from langchain_community.llms import Ollama
except Exception:  # pragma: no cover - optional runtime failure
    Ollama = None

_llm_cache: dict[str, Any] = {}
_llm_lock = threading.Lock()
_adaptive_lock = threading.Lock()
_adaptive_state = {
    "reranker_disabled_until": 0.0,
    "top_k_override_until": 0.0,
    "top_k_override_value": None,
}


def estimate_tokens(text: str) -> int:
    # Lightweight approximation for local models where token counters are unavailable.
    words = len((text or "").split())
    return max(1, int(words * 1.3))


def _build_prompt(context: str, query: str) -> str:
    return (
        system_prompt.replace("{context}", context)
        + "\n\nUser Query: "
        + query.strip()
        + "\nAssistant Response:"
    )


def _filter_docs_for_acl(docs, user):
    # Placeholder for document-level ACL metadata checks.
    # If metadata contains "allowed_roles", enforce it here.
    if not getattr(user, "is_authenticated", False):
        return docs
    user_roles = set(user.groups.values_list("name", flat=True))
    filtered = []
    for doc in docs:
        allowed_roles = doc.metadata.get("allowed_roles")
        if not allowed_roles:
            filtered.append(doc)
            continue
        if set(allowed_roles).intersection(user_roles) or user.is_superuser:
            filtered.append(doc)
    return filtered


def _invoke_local_llm(prompt: str) -> str:
    if Ollama is None:
        return "Local model runtime is unavailable."

    model_name = getattr(settings, "OLLAMA_MODEL", "mistral")
    base_url = getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    cache_key = f"{model_name}|{base_url}"
    with _llm_lock:
        llm = _llm_cache.get(cache_key)
        if llm is None:
            kwargs = {
                "model": model_name,
                "temperature": 0.0,
            }
            if base_url:
                kwargs["base_url"] = base_url
            try:
                llm = Ollama(**kwargs)
            except TypeError:
                kwargs.pop("base_url", None)
                llm = Ollama(**kwargs)
            _llm_cache[cache_key] = llm
    try:
        result = llm.invoke(prompt)
    except Exception as exc:
        return f"I could not generate a response right now. Error: {exc}"
    return str(result).strip()


def _cache_key(query: str, vector_id: str, user) -> str:
    role_sig = ""
    if getattr(user, "is_authenticated", False):
        role_sig = ",".join(sorted(user.groups.values_list("name", flat=True)))
    payload = {
        "q": query,
        "v": vector_id,
        "roles": role_sig,
        "model": getattr(settings, "OLLAMA_MODEL", "mistral"),
        "dense_k": getattr(settings, "RAG_DENSE_K", 30),
        "sparse_k": getattr(settings, "RAG_BM25_K", 30),
        "top_k": getattr(settings, "RAG_TOP_K", 8),
    }
    return "chatq:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z0-9_]+", (text or "").lower()))


def _retrieval_overlap(query: str, docs: list[dict[str, Any]]) -> float:
    q = _tokenize(query)
    if not q:
        return 0.0
    context_words = set()
    for item in docs:
        context_words.update(_tokenize(item.get("content", "")))
    if not context_words:
        return 0.0
    return round(len(q.intersection(context_words)) / max(1, len(q)), 4)


def _citation_coverage(answer: str, sources: list[dict[str, Any]]) -> float:
    urls = [src.get("url", "") for src in sources if src.get("url")]
    if not urls:
        return 0.0
    cited = 0
    for url in urls:
        if url in answer:
            cited += 1
    return round(cited / len(urls), 4)


def _apply_latency_kill_switch(retrieve_ms: int, reranker_in_use: bool, top_k: int) -> None:
    threshold = int(getattr(settings, "RAG_LATENCY_KILL_SWITCH_MS", 1500))
    if retrieve_ms <= threshold:
        return

    ttl_sec = int(getattr(settings, "RAG_ADAPTIVE_DISABLE_TTL_SEC", 60))
    min_top_k = int(getattr(settings, "RAG_MIN_TOP_K", 4))
    new_top_k = max(min_top_k, int(top_k / 2))

    with _adaptive_lock:
        if reranker_in_use:
            _adaptive_state["reranker_disabled_until"] = time.time() + ttl_sec
        _adaptive_state["top_k_override_until"] = time.time() + ttl_sec
        _adaptive_state["top_k_override_value"] = new_top_k


def _adaptive_retrieval_config(load_high: bool) -> tuple[bool, int]:
    now = time.time()
    top_k = int(getattr(settings, "RAG_TOP_K", 8))
    min_top_k = int(getattr(settings, "RAG_MIN_TOP_K", 4))
    reranker_enabled = bool(getattr(settings, "ENABLE_RERANKER", False))

    with _adaptive_lock:
        if now < _adaptive_state["reranker_disabled_until"]:
            reranker_enabled = False
        if now < _adaptive_state["top_k_override_until"] and _adaptive_state["top_k_override_value"]:
            top_k = int(_adaptive_state["top_k_override_value"])

    if load_high:
        top_k = max(min_top_k, int(top_k / 2))
        reranker_enabled = False

    return reranker_enabled, max(min_top_k, top_k)


def _sanitize_links(answer: str, sources: list[dict[str, Any]]) -> str:
    valid_urls = {src.get("url", "") for src in sources if src.get("url")}
    if not valid_urls:
        return answer

    def clean_markdown_links(text: str) -> str:
        def repl(match):
            label, url = match.group(1), match.group(2)
            if url in valid_urls:
                return match.group(0)
            return label

        return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, text)

    def clean_raw_urls(text: str) -> str:
        pattern = re.compile(r"(https?://[^\s)]+)")
        return pattern.sub(lambda m: m.group(1) if m.group(1) in valid_urls else "", text)

    return clean_raw_urls(clean_markdown_links(answer))


def run_secure_chat_query(
    *,
    query: str,
    vector_id: str,
    user,
    trace_id: str,
    session_key: str,
    load_high: bool = False,
) -> dict[str, Any]:
    started = time.perf_counter()
    query = sanitize_text(query)
    blocked, reason = violates_input_policy(query)
    if blocked:
        log_audit(
            trace_id=trace_id,
            actor=user,
            event_type="chat_input_blocked",
            outcome="blocked",
            reason=reason,
            session_key=session_key,
            metadata={"vector_id": vector_id},
        )
        return {
            "answer": safe_block_message(),
            "sources": [],
            "confidence": 0.0,
            "debug": {"reason": reason},
            "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "model_info": {"model": getattr(settings, "OLLAMA_MODEL", "mistral"), "temperature": 0.0},
            "latency_ms": {"total": int((time.perf_counter() - started) * 1000)},
            "blocked": True,
        }

    cache_ttl = int(getattr(settings, "QUERY_CACHE_TTL_SEC", 120))
    enable_query_cache = bool(getattr(settings, "ENABLE_QUERY_CACHE", True))
    ckey = _cache_key(query, vector_id, user)
    if enable_query_cache:
        cached = cache.get(ckey)
        if cached:
            payload = copy.deepcopy(cached)
            payload.setdefault("debug", {})
            payload["debug"]["cache"] = {"hit": True, "key": ckey}
            return payload

    use_reranker, top_k = _adaptive_retrieval_config(load_high)

    t_retrieve_start = time.perf_counter()
    retrieval_error = ""
    try:
        retrieved = hybrid_retrieve(
            vector_id=vector_id,
            query=query,
            top_k=top_k,
            use_reranker=use_reranker,
        )
    except Exception as exc:
        retrieved = []
        retrieval_error = str(exc)
        log_event(
            "chat_retrieval_failed",
            trace_id=trace_id,
            vector_id=vector_id,
            error=retrieval_error,
        )

    retrieved = _filter_docs_for_acl(retrieved, user)
    retrieve_ms = int((time.perf_counter() - t_retrieve_start) * 1000)
    _apply_latency_kill_switch(retrieve_ms, reranker_in_use=use_reranker, top_k=top_k)

    context, selected_docs = compress_context(
        retrieved,
        max_chars=getattr(settings, "RAG_MAX_CONTEXT_CHARS", 9000),
    )
    confidence, confidence_breakdown = confidence_from_docs(selected_docs)

    if not selected_docs:
        no_doc_answer = (
            "Knowledge base is unavailable for the selected collection."
            if retrieval_error
            else "No relevant data found."
        )
        response = {
            "answer": no_doc_answer,
            "sources": [],
            "confidence": 0.0,
            "debug": {
                "retrieved_chunks": [],
                "retrieved_documents": [],
                "reason": "retrieval_failed" if retrieval_error else "no_documents",
                "retrieval_error": retrieval_error,
                "cache": {"hit": False, "key": ckey},
            },
            "token_usage": {
                "prompt_tokens": estimate_tokens(query),
                "completion_tokens": estimate_tokens(no_doc_answer),
                "total_tokens": estimate_tokens(query) + estimate_tokens(no_doc_answer),
            },
            "model_info": {"model": getattr(settings, "OLLAMA_MODEL", "mistral"), "temperature": 0.0},
            "latency_ms": {"retrieval": retrieve_ms, "generation": 0, "total": int((time.perf_counter() - started) * 1000)},
            "blocked": False,
        }
        if enable_query_cache:
            cache.set(ckey, response, timeout=cache_ttl)
        return response

    source_payload = []
    for idx, doc in enumerate(selected_docs, 1):
        source_payload.append(
            {
                "rank": idx,
                "score": round(float(doc.score), 4),
                "retrieval_source": doc.source,
                "url": doc.metadata.get("url", ""),
                "chunk_id": doc.metadata.get("chunk_id", ""),
                "md5": doc.metadata.get("md5", ""),
                "content": (doc.content or "")[:500],
            }
        )

    t_generate_start = time.perf_counter()
    prompt = _build_prompt(context=context, query=query)
    raw_answer = _invoke_local_llm(prompt)
    generate_ms = int((time.perf_counter() - t_generate_start) * 1000)

    safe_answer = sanitize_output(raw_answer)
    blocked_out, out_reason = violates_output_policy(safe_answer)
    if blocked_out:
        log_audit(
            trace_id=trace_id,
            actor=user,
            event_type="chat_output_blocked",
            outcome="blocked",
            reason=out_reason,
            session_key=session_key,
            metadata={"vector_id": vector_id},
        )
        safe_answer = safe_block_message()
        confidence = 0.0

    safe_answer = _sanitize_links(safe_answer, source_payload)

    overlap = _retrieval_overlap(query, source_payload)
    citation_coverage = _citation_coverage(safe_answer, source_payload)
    rerank_margin = float(confidence_breakdown.get("margin", 0.0))
    normalized_margin = max(0.0, min(1.0, rerank_margin * 5.0))
    grounding_score = round(
        min(0.99, 0.45 * overlap + 0.30 * normalized_margin + 0.25 * citation_coverage),
        3,
    )
    confidence = grounding_score

    min_conf = float(getattr(settings, "MIN_CONFIDENCE_TO_ANSWER", 0.25))
    if confidence < min_conf:
        safe_answer = "I'm not confident enough to answer this accurately."

    prompt_tokens = estimate_tokens(prompt)
    completion_tokens = estimate_tokens(safe_answer)
    total_ms = int((time.perf_counter() - started) * 1000)

    debug = {
        "retrieved_chunks": source_payload,
        "retrieved_documents": source_payload,
        "source_links": [src["url"] for src in source_payload if src.get("url")],
        "confidence_breakdown": confidence_breakdown,
        "grounding_score": grounding_score,
        "grounding_factors": {
            "retrieval_overlap": overlap,
            "rerank_margin": round(rerank_margin, 4),
            "citation_coverage": citation_coverage,
        },
        "cache": {"hit": False, "key": ckey},
        "token_usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
        "model_info": {
            "model": getattr(settings, "OLLAMA_MODEL", "mistral"),
            "temperature": 0.0,
            "retrieval": {
                "dense_k": getattr(settings, "RAG_DENSE_K", 30),
                "sparse_k": getattr(settings, "RAG_BM25_K", 30),
                "top_k": top_k,
                "reranker_enabled": use_reranker,
            },
        },
        "latency_ms": {"retrieval": retrieve_ms, "generation": generate_ms, "total": total_ms},
    }

    log_event(
        "chat_query_completed",
        trace_id=trace_id,
        vector_id=vector_id,
        source_count=len(source_payload),
        confidence=confidence,
        latency_ms=debug["latency_ms"],
    )

    response = {
        "answer": safe_answer,
        "sources": source_payload,
        "confidence": confidence,
        "debug": debug,
        "token_usage": debug["token_usage"],
        "model_info": debug["model_info"],
        "latency_ms": debug["latency_ms"],
        "blocked": False,
    }
    if enable_query_cache:
        cache.set(ckey, response, timeout=cache_ttl)
    return response
