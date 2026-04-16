import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0003_remove_chatlog_request_id"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("trace_id", models.CharField(db_index=True, max_length=64)),
                ("prev_hash", models.CharField(blank=True, max_length=64)),
                ("entry_hash", models.CharField(blank=True, db_index=True, max_length=64)),
                ("session_key", models.CharField(blank=True, max_length=100)),
                ("event_type", models.CharField(max_length=80)),
                ("outcome", models.CharField(default="allowed", max_length=20)),
                ("reason", models.CharField(blank=True, max_length=255)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ChatSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(default="New Chat", max_length=200)),
                ("vector_id", models.CharField(max_length=100)),
                ("session_key", models.CharField(db_index=True, max_length=100)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_archived", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="chat_sessions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CrawlJob",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("vector_id", models.CharField(max_length=100)),
                ("url", models.URLField()),
                (
                    "status",
                    models.CharField(
                        choices=[("queued", "Queued"), ("running", "Running"), ("succeeded", "Succeeded"), ("failed", "Failed")],
                        default="queued",
                        max_length=20,
                    ),
                ),
                ("error_message", models.TextField(blank=True)),
                ("result_summary", models.JSONField(blank=True, default=dict)),
                ("trace_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                (
                    "requested_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="crawl_jobs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ChatMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "role",
                    models.CharField(
                        choices=[("user", "User"), ("assistant", "Assistant"), ("system", "System")],
                        max_length=20,
                    ),
                ),
                ("content", models.TextField()),
                ("sources", models.JSONField(blank=True, default=list)),
                ("debug_info", models.JSONField(blank=True, default=dict)),
                ("confidence", models.FloatField(default=0.0)),
                ("model_name", models.CharField(default="mistral", max_length=120)),
                ("prompt_tokens", models.IntegerField(default=0)),
                ("completion_tokens", models.IntegerField(default=0)),
                ("total_tokens", models.IntegerField(default=0)),
                ("latency_ms", models.IntegerField(default=0)),
                ("trace_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "chat_session",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="messages", to="chat.chatsession"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MessageFeedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rating", models.SmallIntegerField(choices=[(1, "Up"), (-1, "Down")])),
                ("correction", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="chat_feedback",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "message",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="feedback", to="chat.chatmessage"),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["event_type", "created_at"], name="chat_auditl_event_t_b0c5ec_idx"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["outcome", "created_at"], name="chat_auditl_outcome_88e790_idx"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["created_at", "entry_hash"], name="chat_auditl_created_7d2ac9_idx"),
        ),
        migrations.AddIndex(
            model_name="chatsession",
            index=models.Index(fields=["vector_id", "created_at"], name="chat_chats_vector__5d5d73_idx"),
        ),
        migrations.AddIndex(
            model_name="chatsession",
            index=models.Index(fields=["session_key", "created_at"], name="chat_chats_session_63bb74_idx"),
        ),
        migrations.AddIndex(
            model_name="crawljob",
            index=models.Index(fields=["status", "created_at"], name="chat_crawlj_status_6d2677_idx"),
        ),
        migrations.AddIndex(
            model_name="crawljob",
            index=models.Index(fields=["vector_id", "created_at"], name="chat_crawlj_vector__f1a2c5_idx"),
        ),
        migrations.AddIndex(
            model_name="chatmessage",
            index=models.Index(fields=["chat_session", "created_at"], name="chat_chatme_chat_se_b22aa9_idx"),
        ),
        migrations.AddIndex(
            model_name="chatmessage",
            index=models.Index(fields=["role", "created_at"], name="chat_chatme_role_12532e_idx"),
        ),
        migrations.AddIndex(
            model_name="messagefeedback",
            index=models.Index(fields=["rating", "created_at"], name="chat_messag_rating_47f8ec_idx"),
        ),
    ]
