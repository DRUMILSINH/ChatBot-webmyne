import { useCallback, useEffect } from "react";

import { createChatSession, fetchDebug, listChatSessions, listMessages, streamMessage } from "./api";
import { useChatStore } from "./store";
import { AppShell } from "./components/AppShell";
import { ChatView } from "./components/ChatView";
import { ErrorBanner } from "./components/ErrorBanner";
import { KnowledgeBaseExplorer } from "./components/KnowledgeBaseExplorer";
import { Sidebar } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";

export function ChatPage() {
  const {
    vectorId,
    chats,
    activeChatId,
    messages,
    streamBuffer,
    isStreaming,
    debugPayload,
    selectedDebugMessageId,
    darkMode,
    error,
    setChats,
    addChat,
    setActiveChat,
    setMessages,
    addMessage,
    setStreaming,
    setStreamBuffer,
    appendStreamBuffer,
    setDebugMessage,
    setDebugPayload,
    toggleDarkMode,
    setError,
  } = useChatStore();

  const loadChats = useCallback(async () => {
    try {
      const sessions = await listChatSessions();
      setChats(sessions);
      if (!activeChatId && sessions.length > 0) {
        setActiveChat(sessions[0].id);
      }
    } catch (err) {
      setError((err as Error).message);
    }
  }, [activeChatId, setActiveChat, setChats, setError]);

  const loadMessages = useCallback(
    async (chatId: string) => {
      try {
        const items = await listMessages(chatId);
        setMessages(items);
      } catch (err) {
        setError((err as Error).message);
      }
    },
    [setError, setMessages]
  );

  useEffect(() => {
    void loadChats();
  }, [loadChats]);

  useEffect(() => {
    if (activeChatId) {
      void loadMessages(activeChatId);
    } else {
      setMessages([]);
    }
  }, [activeChatId, loadMessages, setMessages]);

  useEffect(() => {
    const root = document.documentElement;
    if (darkMode) {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [darkMode]);

  const handleNewChat = useCallback(async () => {
    setError(null);
    try {
      const created = await createChatSession(vectorId, "New Chat");
      addChat(created);
      setActiveChat(created.id);
      setMessages([]);
      setDebugPayload(null);
      setDebugMessage(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }, [addChat, setActiveChat, setDebugMessage, setDebugPayload, setError, setMessages, vectorId]);

  const handleSend = useCallback(
    async (query: string) => {
      setError(null);
      setStreaming(true);
      setStreamBuffer("");

      const tempUserId = Date.now() * -1;
      addMessage({
        id: tempUserId,
        role: "user",
        content: query,
        sources: [],
        created_at: new Date().toISOString(),
      });

      let resolvedChatId = activeChatId;
      if (!resolvedChatId) {
        const created = await createChatSession(vectorId, query.slice(0, 80));
        addChat(created);
        setActiveChat(created.id);
        resolvedChatId = created.id;
      }

      try {
        await streamMessage({
          chatSessionId: resolvedChatId || undefined,
          vectorId,
          query,
          onStart: (payload) => {
            if (!resolvedChatId) {
              setActiveChat(payload.chat_session_id);
            }
          },
          onToken: (token) => appendStreamBuffer(token),
          onDone: (payload) => {
            const retrievedChunks = payload.retrieved_chunks || payload.sources || [];
            addMessage({
              id: payload.assistant_message_id,
              role: "assistant",
              content: payload.answer,
              sources: payload.sources || [],
              confidence: payload.confidence,
              token_usage: payload.token_usage,
              model_info: payload.model_info,
              latency_ms: payload.latency_ms?.total,
              created_at: new Date().toISOString(),
            });
            setDebugMessage(payload.assistant_message_id);
            setDebugPayload({
              confidence: payload.confidence,
              model_info: payload.model_info,
              latency_ms: payload.latency_ms,
              token_usage: payload.token_usage,
              prompt_tokens: payload.prompt_tokens,
              completion_tokens: payload.completion_tokens,
              total_tokens: payload.total_tokens,
              retrieved_chunks: retrievedChunks,
              retrieved_documents: retrievedChunks,
              source_links: retrievedChunks
                .map((item) => item.url || "")
                .filter((url): url is string => Boolean(url)),
            });
            setStreamBuffer("");
            void loadChats();
          },
        });
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setStreaming(false);
      }
    },
    [
      activeChatId,
      addChat,
      addMessage,
      appendStreamBuffer,
      loadChats,
      setActiveChat,
      setError,
      setStreamBuffer,
      setStreaming,
      vectorId,
    ]
  );

  const handleOpenDebug = useCallback(
    async (messageId: number) => {
      setDebugMessage(messageId);
      try {
        const debug = await fetchDebug(messageId);
        setDebugPayload(debug);
      } catch (err) {
        setError((err as Error).message);
      }
    },
    [setDebugMessage, setDebugPayload, setError]
  );

  return (
    <AppShell
      sidebar={
        <Sidebar
          chats={chats}
          activeChatId={activeChatId}
          onSelectChat={(id) => setActiveChat(id)}
          onNewChat={() => void handleNewChat()}
        />
      }
    >
      <TopBar
        title={chats.find((chat) => chat.id === activeChatId)?.title || "New Chat"}
        darkMode={darkMode}
        onToggleTheme={toggleDarkMode}
      />
      <KnowledgeBaseExplorer vectorId={vectorId} />
      {error ? <ErrorBanner message={error} /> : null}
      <ChatView
        messages={messages}
        streamBuffer={streamBuffer}
        isStreaming={isStreaming}
        onSend={handleSend}
        onOpenDebug={(id) => void handleOpenDebug(id)}
        debug={debugPayload}
        selectedMessageId={selectedDebugMessageId}
      />
    </AppShell>
  );
}
