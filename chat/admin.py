from django.contrib import admin

from .models import AuditLog, ChatMessage, ChatSession, CrawlJob, MessageFeedback


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "vector_id", "created_by", "created_at", "updated_at", "is_archived")
    search_fields = ("id", "title", "vector_id", "session_key")
    list_filter = ("vector_id", "is_archived", "created_at")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "chat_session", "role", "confidence", "model_name", "latency_ms", "created_at")
    search_fields = ("content", "trace_id")
    list_filter = ("role", "model_name", "created_at")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "event_type", "outcome", "trace_id", "entry_hash", "actor", "created_at")
    search_fields = ("trace_id", "event_type", "reason", "entry_hash", "prev_hash")
    list_filter = ("event_type", "outcome", "created_at")


@admin.register(CrawlJob)
class CrawlJobAdmin(admin.ModelAdmin):
    list_display = ("id", "vector_id", "status", "requested_by", "created_at", "finished_at")
    search_fields = ("id", "vector_id", "url", "trace_id")
    list_filter = ("status", "vector_id", "created_at")


@admin.register(MessageFeedback)
class MessageFeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "rating", "created_by", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("message__content", "correction")
