import { useEffect, useRef } from "react";

import { ChatMessage } from "../types";
import { EmptyState } from "./EmptyState";
import { MessageBubble } from "./MessageBubble";
import { RichText } from "./RichText";

type MessageListProps = {
  messages: ChatMessage[];
  streamingContent: string;
  onOpenDebug: (id: number) => void;
};

export function MessageList({ messages, streamingContent, onOpenDebug }: MessageListProps) {
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages, streamingContent]);

  return (
    <div ref={listRef} className="min-h-0 flex-1 overflow-y-auto p-4">
      {messages.length === 0 && !streamingContent ? (
        <EmptyState />
      ) : (
        <>
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} onOpenDebug={onOpenDebug} />
          ))}
          {streamingContent ? (
            <div className="mb-3 flex justify-start">
              <div className="max-w-[82%] rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm dark:border-slate-700 dark:bg-slate-800">
                <RichText text={streamingContent} />
              </div>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
