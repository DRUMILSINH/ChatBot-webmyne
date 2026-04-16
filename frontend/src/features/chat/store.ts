import { create } from "zustand";

import { ChatMessage, ChatSession, DebugPayload } from "./types";

type ChatState = {
  vectorId: string;
  chats: ChatSession[];
  activeChatId: string | null;
  messages: ChatMessage[];
  isLoading: boolean;
  isStreaming: boolean;
  streamBuffer: string;
  selectedDebugMessageId: number | null;
  debugPayload: DebugPayload | null;
  darkMode: boolean;
  error: string | null;
  setChats: (items: ChatSession[]) => void;
  addChat: (chat: ChatSession) => void;
  setActiveChat: (chatId: string | null) => void;
  setMessages: (items: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  setLoading: (value: boolean) => void;
  setStreaming: (value: boolean) => void;
  setStreamBuffer: (value: string) => void;
  appendStreamBuffer: (token: string) => void;
  setDebugMessage: (messageId: number | null) => void;
  setDebugPayload: (payload: DebugPayload | null) => void;
  toggleDarkMode: () => void;
  setError: (text: string | null) => void;
};

const persistedTheme = window.localStorage.getItem("chat_ui_theme") || "dark";

export const useChatStore = create<ChatState>((set) => ({
  vectorId: "webmyne",
  chats: [],
  activeChatId: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  streamBuffer: "",
  selectedDebugMessageId: null,
  debugPayload: null,
  darkMode: persistedTheme === "dark",
  error: null,
  setChats: (items) => set({ chats: items }),
  addChat: (chat) =>
    set((state) => ({
      chats: [chat, ...state.chats.filter((item) => item.id !== chat.id)],
    })),
  setActiveChat: (chatId) => set({ activeChatId: chatId }),
  setMessages: (items) => set({ messages: items }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setLoading: (value) => set({ isLoading: value }),
  setStreaming: (value) => set({ isStreaming: value }),
  setStreamBuffer: (value) => set({ streamBuffer: value }),
  appendStreamBuffer: (token) => set((state) => ({ streamBuffer: state.streamBuffer + token })),
  setDebugMessage: (messageId) => set({ selectedDebugMessageId: messageId }),
  setDebugPayload: (payload) => set({ debugPayload: payload }),
  toggleDarkMode: () =>
    set((state) => {
      const next = !state.darkMode;
      window.localStorage.setItem("chat_ui_theme", next ? "dark" : "light");
      return { darkMode: next };
    }),
  setError: (text) => set({ error: text }),
}));
