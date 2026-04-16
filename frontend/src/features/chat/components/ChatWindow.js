import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Composer } from './Composer';
import { MessageList } from './MessageList';
export function ChatWindow({ messages, streamBuffer, isStreaming, onSend, onOpenDebug }) {
    return (_jsxs("div", { className: "flex min-h-0 flex-1 flex-col", children: [_jsx(MessageList, { messages: messages, streamingContent: streamBuffer, onOpenDebug: onOpenDebug }), _jsx(Composer, { disabled: isStreaming, onSend: onSend })] }));
}
