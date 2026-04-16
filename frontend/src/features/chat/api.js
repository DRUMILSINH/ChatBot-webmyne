function getCookie(name) {
    const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
    return match ? decodeURIComponent(match[2]) : "";
}
async function ensureCsrfCookie() {
    await fetch("/api/v2/auth/csrf", {
        method: "GET",
        credentials: "include",
    });
}
async function requestJson(url, init = {}) {
    const csrf = getCookie("csrftoken");
    const headers = new Headers(init.headers || {});
    if (!headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }
    if (csrf) {
        headers.set("X-CSRFToken", csrf);
    }
    const response = await fetch(url, {
        ...init,
        headers,
        credentials: "include",
    });
    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || `Request failed (${response.status})`);
    }
    return response.json();
}
export async function createChatSession(vectorId, title) {
    await ensureCsrfCookie();
    const payload = await requestJson("/api/v2/chats", {
        method: "POST",
        body: JSON.stringify({ vector_id: vectorId, title: title || "New Chat" }),
    });
    return payload.chat;
}
export async function listChatSessions() {
    const payload = await requestJson("/api/v2/chats");
    return payload.items;
}
export async function listMessages(chatId) {
    const payload = await requestJson(`/api/v2/chats/${chatId}/messages`);
    return payload.items;
}
export async function sendMessage(chatId, query, vectorId) {
    await ensureCsrfCookie();
    const payload = await requestJson(`/api/v2/chats/${chatId}/messages`, {
        method: "POST",
        body: JSON.stringify({ query, vector_id: vectorId }),
    });
    return {
        id: payload.assistant_message_id,
        role: "assistant",
        content: payload.answer,
        sources: payload.sources || [],
        confidence: payload.confidence,
        token_usage: payload.token_usage,
        model_info: payload.model_info,
        latency_ms: payload.latency_ms?.total,
        created_at: new Date().toISOString(),
    };
}
export async function streamMessage(options) {
    await ensureCsrfCookie();
    const csrf = getCookie("csrftoken");
    const response = await fetch("/api/v2/chat/stream", {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
            ...(csrf ? { "X-CSRFToken": csrf } : {}),
        },
        body: JSON.stringify({
            chat_session_id: options.chatSessionId,
            vector_id: options.vectorId,
            query: options.query,
        }),
    });
    if (!response.ok || !response.body) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || "Streaming failed.");
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
        const { done, value } = await reader.read();
        if (done)
            break;
        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\n\n");
        buffer = chunks.pop() || "";
        for (const chunk of chunks) {
            const lines = chunk.split("\n");
            const event = lines.find((line) => line.startsWith("event:"))?.replace("event:", "").trim();
            const dataLine = lines.find((line) => line.startsWith("data:"))?.replace("data:", "").trim();
            if (!event || !dataLine)
                continue;
            const data = JSON.parse(dataLine);
            if (event === "start") {
                options.onStart?.(data);
            }
            else if (event === "token") {
                options.onToken(data.token || "");
            }
            else if (event === "done") {
                options.onDone(data);
            }
        }
    }
}
export async function fetchDebug(messageId) {
    const payload = await requestJson(`/api/v2/chat/debug/${messageId}`);
    return payload.debug;
}
export async function fetchKnowledgeBaseStats(vectorId) {
    const query = new URLSearchParams({ vector_id: vectorId });
    return requestJson(`/api/v2/knowledge-base/stats/?${query.toString()}`);
}
