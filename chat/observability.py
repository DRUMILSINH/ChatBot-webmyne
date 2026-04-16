import json
import logging
import hashlib
import time
from typing import Any

from django.db import transaction

from chat.models import AuditLog


logger = logging.getLogger("chat.observability")


def log_event(event: str, trace_id: str = "", level: str = "info", **kwargs: Any) -> None:
    payload = {"event": event, "trace_id": trace_id, **kwargs}
    message = json.dumps(payload, ensure_ascii=False, default=str)

    if level == "error":
        logger.error(message)
    elif level == "warning":
        logger.warning(message)
    else:
        logger.info(message)


def log_audit(
    *,
    trace_id: str,
    event_type: str,
    outcome: str = AuditLog.OUTCOME_ALLOWED,
    actor=None,
    session_key: str = "",
    reason: str = "",
    metadata: dict | None = None,
) -> None:
    metadata = metadata or {}
    try:
        actor_ref = actor if getattr(actor, "is_authenticated", False) else None
        with transaction.atomic():
            previous = (
                AuditLog.objects.select_for_update()
                .order_by("-id")
                .values_list("entry_hash", flat=True)
                .first()
            ) or ("0" * 64)
            row = AuditLog.objects.create(
                trace_id=trace_id,
                prev_hash=previous,
                entry_hash="",
                actor=actor_ref,
                session_key=session_key,
                event_type=event_type,
                outcome=outcome,
                reason=reason,
                metadata=metadata,
            )
            canonical = json.dumps(
                {
                    "id": row.id,
                    "trace_id": row.trace_id,
                    "actor_id": row.actor_id,
                    "session_key": row.session_key,
                    "event_type": row.event_type,
                    "outcome": row.outcome,
                    "reason": row.reason,
                    "metadata": row.metadata or {},
                    "created_at": row.created_at.isoformat(),
                },
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            )
            row.entry_hash = hashlib.sha256((previous + canonical).encode("utf-8")).hexdigest()
            row.save(update_fields=["entry_hash"])
    except Exception as exc:
        log_event(
            "audit_write_failed",
            trace_id=trace_id,
            level="error",
            error=str(exc),
            event_type=event_type,
        )


def verify_audit_chain(limit: int = 5000) -> tuple[bool, str]:
    """
    Verifies tamper-evident hash chaining for the latest audit rows.
    """
    previous = "0" * 64
    rows = AuditLog.objects.order_by("id")[:limit]
    for row in rows:
        canonical = json.dumps(
            {
                "id": row.id,
                "trace_id": row.trace_id,
                "actor_id": row.actor_id,
                "session_key": row.session_key,
                "event_type": row.event_type,
                "outcome": row.outcome,
                "reason": row.reason,
                "metadata": row.metadata or {},
                "created_at": row.created_at.isoformat(),
            },
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
        expected = hashlib.sha256((previous + canonical).encode("utf-8")).hexdigest()
        if row.prev_hash != previous or row.entry_hash != expected:
            return False, f"chain_break_at_id:{row.id}"
        previous = row.entry_hash or expected
    return True, "ok"


def now_ms() -> float:
    return time.perf_counter() * 1000.0
