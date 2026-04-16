import uuid

from django.conf import settings
from django.db import models

class PersonalInfo(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    device_type = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.session_id}"


class ChatLog(models.Model):
    # session_id = models.CharField(max_length=100)
    session = models.ForeignKey(PersonalInfo, on_delete=models.CASCADE)

    user_query = models.TextField()
    response = models.TextField()
    response_time = models.FloatField()
    # device_type = models.CharField(max_length=20)
    vector_id = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'chat'

class ClickedURL(models.Model):
    session = models.ForeignKey(PersonalInfo, on_delete=models.CASCADE)
    url = models.URLField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.url} - {self.session.session_id}"


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, default="New Chat")
    vector_id = models.CharField(max_length=100)
    session_key = models.CharField(max_length=100, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="chat_sessions",
    )
    metadata = models.JSONField(default=dict, blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["vector_id", "created_at"]),
            models.Index(fields=["session_key", "created_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.vector_id})"


class ChatMessage(models.Model):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_SYSTEM = "system"
    ROLE_CHOICES = [
        (ROLE_USER, "User"),
        (ROLE_ASSISTANT, "Assistant"),
        (ROLE_SYSTEM, "System"),
    ]

    chat_session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    debug_info = models.JSONField(default=dict, blank=True)
    confidence = models.FloatField(default=0.0)
    model_name = models.CharField(max_length=120, default="mistral")
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    latency_ms = models.IntegerField(default=0)
    trace_id = models.CharField(max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["chat_session", "created_at"]),
            models.Index(fields=["role", "created_at"]),
        ]

    def __str__(self):
        return f"{self.role} @ {self.created_at.isoformat()}"


class AuditLog(models.Model):
    OUTCOME_ALLOWED = "allowed"
    OUTCOME_BLOCKED = "blocked"
    OUTCOME_ERROR = "error"

    trace_id = models.CharField(max_length=64, db_index=True)
    prev_hash = models.CharField(max_length=64, blank=True)
    entry_hash = models.CharField(max_length=64, blank=True, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    session_key = models.CharField(max_length=100, blank=True)
    event_type = models.CharField(max_length=80)
    outcome = models.CharField(max_length=20, default=OUTCOME_ALLOWED)
    reason = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["outcome", "created_at"]),
            models.Index(fields=["created_at", "entry_hash"]),
        ]

    def __str__(self):
        return f"{self.event_type}:{self.outcome}"


class CrawlJob(models.Model):
    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_QUEUED, "Queued"),
        (STATUS_RUNNING, "Running"),
        (STATUS_SUCCEEDED, "Succeeded"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="crawl_jobs",
    )
    vector_id = models.CharField(max_length=100)
    url = models.URLField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    error_message = models.TextField(blank=True)
    result_summary = models.JSONField(default=dict, blank=True)
    trace_id = models.CharField(max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["vector_id", "created_at"]),
        ]

    def __str__(self):
        return f"{self.vector_id}::{self.status}"


class MessageFeedback(models.Model):
    RATING_UP = 1
    RATING_DOWN = -1
    RATING_CHOICES = [
        (RATING_UP, "Up"),
        (RATING_DOWN, "Down"),
    ]

    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name="feedback")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="chat_feedback",
    )
    rating = models.SmallIntegerField(choices=RATING_CHOICES)
    correction = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["rating", "created_at"]),
        ]

    def __str__(self):
        return f"feedback:{self.rating}:{self.message_id}"
