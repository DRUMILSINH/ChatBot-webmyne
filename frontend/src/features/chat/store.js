import { create } from "zustand";
const persistedTheme = window.localStorage.getItem("chat_ui_theme") || "dark";
export const useChatStore = create((set) => ({
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
    addChat: (chat) => set((state) => ({
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
    toggleDarkMode: () => set((state) => {
        const next = !state.darkMode;
        window.localStorage.setItem("chat_ui_theme", next ? "dark" : "light");
        return { darkMode: next };
    }),
    setError: (text) => set({ error: text }),
}));
