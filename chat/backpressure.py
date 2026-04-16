import threading
from contextlib import contextmanager

from django.conf import settings

from chat.models import CrawlJob


class StreamLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        self._active_streams = 0

    @property
    def active_streams(self) -> int:
        with self._lock:
            return self._active_streams

    @contextmanager
    def acquire(self):
        with self._lock:
            self._active_streams += 1
        try:
            yield
        finally:
            with self._lock:
                self._active_streams = max(0, self._active_streams - 1)

    def has_capacity(self) -> bool:
        limit = int(getattr(settings, "MAX_CONCURRENT_STREAMS", 50))
        return self.active_streams < limit


stream_limiter = StreamLimiter()


def queue_depth() -> int:
    return CrawlJob.objects.filter(
        status__in=[CrawlJob.STATUS_QUEUED, CrawlJob.STATUS_RUNNING]
    ).count()


def user_queue_depth(user) -> int:
    if not getattr(user, "is_authenticated", False):
        return queue_depth()
    return CrawlJob.objects.filter(
        requested_by=user,
        status__in=[CrawlJob.STATUS_QUEUED, CrawlJob.STATUS_RUNNING],
    ).count()


def high_load() -> bool:
    stream_threshold = int(getattr(settings, "HIGH_LOAD_STREAM_THRESHOLD", 20))
    queue_threshold = int(getattr(settings, "HIGH_LOAD_QUEUE_THRESHOLD", 40))
    return stream_limiter.active_streams >= stream_threshold or queue_depth() >= queue_threshold
