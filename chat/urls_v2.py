from django.urls import path

from . import views_v2


urlpatterns = [
    path("auth/csrf", views_v2.csrf_bootstrap, name="v2_csrf_bootstrap"),
    path("knowledge-base/stats/", views_v2.knowledge_base_stats, name="v2_knowledge_base_stats"),
    path("chats", views_v2.chats, name="v2_chats"),
    path("chats/<uuid:chat_id>/messages", views_v2.chat_messages, name="v2_chat_messages"),
    path("chat/stream", views_v2.chat_stream, name="v2_chat_stream"),
    path("chat/feedback", views_v2.chat_feedback, name="v2_chat_feedback"),
    path("chat/debug/<int:message_id>", views_v2.chat_debug, name="v2_chat_debug"),
]
