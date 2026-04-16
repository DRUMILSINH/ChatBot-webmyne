import hashlib
import json
import math
import re
import time
from dataclasses import dataclass
from typing import Any

from django.conf import settings

from chatbot.vector_store import get_vector_store

try:
    from rank_bm25 import BM25Okapi
except Exception:  # pragma: no cover - optional dependency
    BM25Okapi = None

try:
    from sentence_transformers import CrossEncoder
except Exception:  # pragma: no cover - optional dependency
    CrossEncoder = None


_reranker_model = None
_bm25_cache: dict[str, dict[str, Any]] = {}
_hybrid_cache: dict[str, tuple[float, list["ScoredDoc"]]] = {}


@dataclass
class ScoredDoc:
    content: str
    metadata: dict
    score: float
    source: str


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_]+", text.lower())


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return fallback


def _dense_retrieve(vector_id: str, query: str, k: int) -> list[ScoredDoc]:
    vector_store = get_vector_store(vector_id)
    docs: list[ScoredDoc] = []

    try:
        results = vector_store.similarity_search_with_score(query, k=k)

        def normalize_dense_score(raw_value: Any) -> float:
            value = _safe_float(raw_value, 1.0)
            if not math.isfinite(value):
                return 0.0

            # Chroma commonly returns distances (lower is better).
            # Convert to bounded similarity for consistent confidence math.
            if value >= 0:
                return 1.0 / (1.0 + value)

            # Defensive handling for stores that return cosine similarity in [-1, 1].
            if -1.0 <= value < 0:
                return (value + 1.0) / 2.0

            return 0.0

        for doc, raw_score in results:
            score = normalize_dense_score(raw_score)
            docs.append(
                ScoredDoc(
                    content=doc.page_content,
                    metadata=doc.metadata or {},
                    score=score,
                    source="dense",
                )
            )
        return docs
    except Exception:
        pass

    for doc in vector_store.similarity_search(query, k=k):
        docs.append(
            ScoredDoc(
                content=doc.page_content,
                metadata=doc.metadata or {},
                score=0.3,
                source="dense",
            )
        )
    return docs


def _build_sparse_index(vector_id: str) -> dict[str, Any]:
    vector_store = get_vector_store(vector_id)
    payload = vector_store.get(include=["documents", "metadatas"])
    docs = payload.get("documents") or []
    metas = payload.get("metadatas") or []

    tokenized = [_tokenize(text or "") for text in docs]
    checksum = hash(tuple((len(d or ""), (metas[i] or {}).get("chunk_id", i)) for i, d in enumerate(docs)))

    cached = _bm25_cache.get(vector_id)
    if cached and cached.get("checksum") == checksum:
        return cached

    index = {
        "checksum": checksum,
        "docs": docs,
        "metadatas": metas,
        "tokens": tokenized,
        "bm25": BM25Okapi(tokenized) if BM25Okapi and docs else None,
    }
    _bm25_cache[vector_id] = index
    return index


def _sparse_retrieve(vector_id: str, query: str, k: int) -> list[ScoredDoc]:
    index = _build_sparse_index(vector_id)
    docs = index["docs"]
    metadatas = index["metadatas"]
    tokens = index["tokens"]
    if not docs:
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    if index["bm25"] is not None:
        raw_scores = index["bm25"].get_scores(query_tokens)
    else:
        # Fallback lexical score if rank_bm25 is unavailable.
        raw_scores = []
        query_token_set = set(query_tokens)
        for doc_tokens in tokens:
            if not doc_tokens:
                raw_scores.append(0.0)
                continue
            overlap = len(query_token_set.intersection(doc_tokens))
            raw_scores.append(overlap / math.sqrt(len(doc_tokens)))

    ranked = sorted(enumerate(raw_scores), key=lambda item: item[1], reverse=True)[:k]
    best = max([score for _, score in ranked], default=0.0)
    norm = best if best > 0 else 1.0

    sparse_docs: list[ScoredDoc] = []
    for idx, score in ranked:
        sparse_docs.append(
            ScoredDoc(
                content=docs[idx] or "",
                metadata=(metadatas[idx] or {}),
                score=float(score) / norm,
                source="sparse",
            )
        )
    return sparse_docs


def _doc_key(doc: ScoredDoc) -> str:
    md5 = doc.metadata.get("md5")
    if md5:
        return str(md5)
    chunk_id = doc.metadata.get("chunk_id")
    if chunk_id:
        return str(chunk_id)
    return f"{doc.metadata.get('url', '')}:{hash(doc.content)}"


def _rrf_fuse(dense: list[ScoredDoc], sparse: list[ScoredDoc], rrf_k: int = 60) -> list[ScoredDoc]:
    merged: dict[str, dict[str, Any]] = {}

    def add_docs(items: list[ScoredDoc]) -> None:
        for rank, item in enumerate(items, 1):
            key = _doc_key(item)
            score = 1.0 / (rrf_k + rank)
            if key not in merged:
                merged[key] = {
                    "doc": item,
                    "score": score,
                    "sources": {item.source},
                }
            else:
                merged[key]["score"] += score
                merged[key]["sources"].add(item.source)
                if item.score > merged[key]["doc"].score:
                    merged[key]["doc"] = item

    add_docs(dense)
    add_docs(sparse)

    fused: list[ScoredDoc] = []
    for value in merged.values():
        doc = value["doc"]
        fused.append(
            ScoredDoc(
                content=doc.content,
                metadata=doc.metadata,
                score=value["score"],
                source="+".join(sorted(value["sources"])),
            )
        )
    fused.sort(key=lambda item: item.score, reverse=True)
    return fused


def _get_reranker():
    global _reranker_model
    if _reranker_model is not None:
        return _reranker_model
    if not CrossEncoder:
        return None
    try:
        _reranker_model = CrossEncoder(settings.RERANKER_MODEL)
    except Exception:
        _reranker_model = None
    return _reranker_model


def _rerank(query: str, docs: list[ScoredDoc], top_k: int, use_reranker: bool | None = None) -> list[ScoredDoc]:
    if not docs:
        return []

    if use_reranker is None:
        use_reranker = getattr(settings, "ENABLE_RERANKER", False)

    if not use_reranker:
        return docs[:top_k]

    model = _get_reranker()
    if model is None:
        return docs[:top_k]

    pairs = [[query, d.content[:1800]] for d in docs]
    try:
        scores = model.predict(pairs)
    except Exception:
        return docs[:top_k]

    ranked = sorted(
        zip(docs, scores),
        key=lambda item: float(item[1]),
        reverse=True,
    )[:top_k]
    return [
        ScoredDoc(
            content=item[0].content,
            metadata=item[0].metadata,
            score=float(item[1]),
            source=item[0].source + "+rerank",
        )
        for item in ranked
    ]


def compress_context(docs: list[ScoredDoc], max_chars: int) -> tuple[str, list[ScoredDoc]]:
    seen = set()
    selected = []
    context_parts: list[str] = []
    current = 0

    for rank, doc in enumerate(docs, 1):
        snippet = (doc.content or "").strip()
        if not snippet:
            continue
        normalized = re.sub(r"\s+", " ", snippet)
        sig = hash(normalized[:500])
        if sig in seen:
            continue
        seen.add(sig)

        section = f"[Doc {rank}] {normalized}"
        if current + len(section) > max_chars:
            break
        context_parts.append(section)
        current += len(section)
        selected.append(doc)

    return "\n\n".join(context_parts), selected


def hybrid_retrieve(
    *,
    vector_id: str,
    query: str,
    dense_k: int | None = None,
    sparse_k: int | None = None,
    top_k: int | None = None,
    use_reranker: bool | None = None,
) -> list[ScoredDoc]:
    dense_k = dense_k or getattr(settings, "RAG_DENSE_K", 30)
    sparse_k = sparse_k or getattr(settings, "RAG_BM25_K", 30)
    top_k = top_k or getattr(settings, "RAG_TOP_K", 8)

    cache_enabled = getattr(settings, "ENABLE_RETRIEVAL_CACHE", True)
    cache_ttl = int(getattr(settings, "RETRIEVAL_CACHE_TTL_SEC", 60))
    cache_key = hashlib.sha256(
        json.dumps(
            {
                "vector_id": vector_id,
                "query": query,
                "dense_k": dense_k,
                "sparse_k": sparse_k,
                "top_k": top_k,
                "rerank": use_reranker,
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()

    if cache_enabled:
        cached = _hybrid_cache.get(cache_key)
        if cached and time.time() - cached[0] <= cache_ttl:
            return cached[1]

    dense_docs = _dense_retrieve(vector_id, query, dense_k)
    sparse_docs = _sparse_retrieve(vector_id, query, sparse_k)
    fused = _rrf_fuse(dense_docs, sparse_docs)
    ranked = _rerank(query, fused, top_k, use_reranker=use_reranker)
    if cache_enabled:
        _hybrid_cache[cache_key] = (time.time(), ranked)
    return ranked


def confidence_from_docs(docs: list[ScoredDoc]) -> tuple[float, dict]:
    if not docs:
        return 0.0, {"reason": "no_documents"}
    top_score = docs[0].score
    source_count = len(docs)
    margin = docs[0].score - (docs[1].score if len(docs) > 1 else 0.0)
    confidence = min(0.99, max(0.05, 0.45 * top_score + 0.1 * min(source_count, 5) + 0.45 * margin))
    return round(confidence, 3), {
        "top_score": round(top_score, 4),
        "margin": round(margin, 4),
        "source_count": source_count,
    }
