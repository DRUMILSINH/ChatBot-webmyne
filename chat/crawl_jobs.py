from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.utils import timezone

from chat.models import CrawlJob
from chat.observability import log_audit, log_event
from chatbot.pipeline import crawl_and_embed

_executor = ThreadPoolExecutor(
    max_workers=int(getattr(settings, "MAX_PARALLEL_CRAWL_WORKERS", 4))
)


def _run_job(job_id: str) -> None:
    job = CrawlJob.objects.get(id=job_id)
    job.status = CrawlJob.STATUS_RUNNING
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at", "updated_at"])

    try:
        result = crawl_and_embed(
            url=job.url,
            vector_id=job.vector_id,
            max_pages=getattr(settings, "CRAWL_MAX_PAGES", 20),
            embed=True,
        )
        job.status = CrawlJob.STATUS_SUCCEEDED
        job.result_summary = result
        job.error_message = ""
        outcome = "allowed"
        reason = ""
    except Exception as exc:
        job.status = CrawlJob.STATUS_FAILED
        job.error_message = str(exc)
        job.result_summary = {}
        outcome = "error"
        reason = str(exc)

    job.finished_at = timezone.now()
    job.save(
        update_fields=["status", "result_summary", "error_message", "finished_at", "updated_at"]
    )

    log_event(
        "crawl_job_finished",
        trace_id=job.trace_id,
        job_id=str(job.id),
        status=job.status,
        vector_id=job.vector_id,
    )
    log_audit(
        trace_id=job.trace_id,
        actor=job.requested_by,
        event_type="crawl_job_finished",
        outcome=outcome,
        reason=reason,
        metadata={"job_id": str(job.id), "vector_id": job.vector_id, "status": job.status},
    )


def enqueue_crawl_job(job: CrawlJob) -> None:
    _executor.submit(_run_job, str(job.id))
