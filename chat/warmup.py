import threading

from django.conf import settings

from chatbot.retrieval import hybrid_retrieve

try:
    from chat.services_v2 import _invoke_local_llm
except Exception:  # pragma: no cover
    _invoke_local_llm = None


def _warmup() -> None:
    vector_ids = getattr(settings, "PRELOAD_VECTOR_IDS", []) or []
    for vector_id in vector_ids:
        try:
            hybrid_retrieve(
                vector_id=vector_id,
                query="company overview",
                dense_k=4,
                sparse_k=4,
                top_k=2,
                use_reranker=False,
            )
        except Exception:
            continue

    if _invoke_local_llm:
        try:
            _invoke_local_llm("Say 'ready'.")
        except Exception:
            pass


def start_cold_start_preload() -> None:
    if not getattr(settings, "ENABLE_COLD_START_PRELOAD", False):
        return
    t = threading.Thread(target=_warmup, daemon=True)
    t.start()
