import json
import re
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.test import TestCase, override_settings
from django.urls import reverse

from chat.models import ChatMessage, ChatSession


class ChatV2ApiTests(TestCase):
    databases = {"default", "logs"}

    @patch("chat.views_v2.run_secure_chat_query")
    def test_create_session_and_post_message(self, mocked_run):
        mocked_run.return_value = {
            "answer": "Test answer",
            "sources": [{"url": "https://example.com", "chunk_id": "1", "md5": "x", "score": 0.9, "rank": 1, "retrieval_source": "dense", "content": "sample"}],
            "confidence": 0.8,
            "debug": {"retrieved_chunks": [{"url": "https://example.com", "chunk_id": "1", "score": 0.9, "content": "sample"}]},
            "token_usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "model_info": {"model": "mistral"},
            "latency_ms": {"total": 12, "retrieval": 5, "generation": 7},
            "blocked": False,
        }

        create_res = self.client.post(
            reverse("v2_chats"),
            data=json.dumps({"title": "My Chat", "vector_id": "webmyne"}),
            content_type="application/json",
        )
        self.assertEqual(create_res.status_code, 201)
        chat_id = create_res.json()["chat"]["id"]

        msg_res = self.client.post(
            reverse("v2_chat_messages", kwargs={"chat_id": chat_id}),
            data=json.dumps({"query": "What services do you provide?"}),
            content_type="application/json",
        )
        self.assertEqual(msg_res.status_code, 200)
        payload = msg_res.json()
        self.assertEqual(payload["answer"], "Test answer")
        self.assertEqual(payload["prompt_tokens"], 10)
        self.assertEqual(payload["completion_tokens"], 5)
        self.assertEqual(payload["latency_ms"]["total"], 12)
        self.assertEqual(len(payload["retrieved_chunks"]), 1)
        self.assertEqual(ChatSession.objects.count(), 1)
        self.assertEqual(ChatMessage.objects.count(), 2)

        feedback_res = self.client.post(
            reverse("v2_chat_feedback"),
            data=json.dumps({"message_id": payload["assistant_message_id"], "rating": 1}),
            content_type="application/json",
        )
        self.assertEqual(feedback_res.status_code, 201)

    @override_settings(SSE_REQUIRE_ASGI=False)
    @patch("chat.views_v2.run_secure_chat_query")
    def test_stream_endpoint_returns_sse(self, mocked_run):
        mocked_run.return_value = {
            "answer": "hello world",
            "sources": [{"url": "https://example.com", "chunk_id": "x", "score": 0.5, "content": "hello"}],
            "confidence": 0.5,
            "debug": {"retrieved_chunks": [{"url": "https://example.com", "chunk_id": "x", "score": 0.5, "content": "hello"}]},
            "token_usage": {"prompt_tokens": 2, "completion_tokens": 2, "total_tokens": 4},
            "model_info": {"model": "mistral"},
            "latency_ms": {"total": 5, "retrieval": 2, "generation": 3},
            "blocked": False,
        }
        response = self.client.post(
            reverse("v2_chat_stream"),
            data=json.dumps({"query": "hello", "vector_id": "webmyne"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        body = b"".join(response.streaming_content).decode("utf-8")
        self.assertIn("event: start", body)
        self.assertIn("event: token", body)
        self.assertIn("event: done", body)
        done_matches = re.findall(r"event: done\ndata: (.+)", body)
        self.assertTrue(done_matches)
        done_payload = json.loads(done_matches[-1])
        self.assertEqual(done_payload["prompt_tokens"], 2)
        self.assertEqual(done_payload["completion_tokens"], 2)
        self.assertEqual(done_payload["latency_ms"]["total"], 5)
        self.assertEqual(len(done_payload["retrieved_chunks"]), 1)

    @override_settings(ENFORCE_RBAC=True)
    def test_debug_endpoint_requires_analyst_role(self):
        user = User.objects.create_user(username="plain", password="pwd")
        self.client.force_login(user)
        response = self.client.get(reverse("v2_chat_debug", kwargs={"message_id": 1}))
        self.assertEqual(response.status_code, 403)

    def test_debug_endpoint_sanitizes_chunk_content(self):
        analyst_group, _ = Group.objects.get_or_create(name="chat_analyst")
        user = User.objects.create_user(username="analyst", password="pwd")
        user.groups.add(analyst_group)
        self.client.force_login(user)

        chat = ChatSession.objects.create(
            title="Debug Test",
            vector_id="webmyne",
            session_key="abc123",
            created_by=user,
        )
        msg = ChatMessage.objects.create(
            chat_session=chat,
            role=ChatMessage.ROLE_ASSISTANT,
            content="safe",
            debug_info={
                "retrieved_documents": [
                    {
                        "content": "Contact john.doe@example.com and account 12345678910",
                        "url": "https://example.com",
                    }
                ]
            },
        )

        response = self.client.get(reverse("v2_chat_debug", kwargs={"message_id": msg.id}))
        self.assertEqual(response.status_code, 200)
        redacted = response.json()["debug"]["retrieved_documents"][0]["content"]
        self.assertIn("[REDACTED]", redacted)
        self.assertIn("[REDACTED_NUM]", redacted)

    @patch("chat.views_v2.get_vector_store")
    def test_knowledge_base_stats_endpoint(self, mocked_get_vector_store):
        class FakeCollection:
            @staticmethod
            def count():
                return 4

        class FakeVectorStore:
            _collection = FakeCollection()

            @staticmethod
            def get(include=None):
                return {
                    "metadatas": [
                        {"url": "https://example.com/a", "chunk_id": "a1"},
                        {"url": "https://example.com/a", "chunk_id": "a2"},
                        {"url": "https://example.com/b", "chunk_id": "b1"},
                        {"chunk_id": "missing-url"},
                    ]
                }

        mocked_get_vector_store.return_value = FakeVectorStore()

        response = self.client.get(reverse("v2_knowledge_base_stats"), {"vector_id": "webmyne"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["vector_id"], "webmyne")
        self.assertEqual(payload["total_vectors"], 4)
        self.assertEqual(payload["total_chunks"], 4)
        self.assertEqual(payload["unique_urls"], 2)
        self.assertEqual(payload["chunks_with_source_url"], 3)
        self.assertEqual(payload["chunks_without_source_url"], 1)
        self.assertEqual(payload["top_sources"][0]["url"], "https://example.com/a")
        self.assertEqual(payload["top_sources"][0]["chunk_count"], 2)
