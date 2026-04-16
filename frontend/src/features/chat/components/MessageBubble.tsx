import clsx from "clsx";

import { ChatMessage } from "../types";
import { RichText } from "./RichText";

type MessageBubbleProps = {
  message: ChatMessage;
  onOpenDebug: (id: number) => void;
};

export function MessageBubble({ message, onOpenDebug }: MessageBubbleProps) {
  const isUser = message.role === "user";
  return (
    <div className={clsx("mb-3 flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={clsx(
          "max-w-[82%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isUser
            ? "bg-brand-600 text-white"
            : "border border-slate-200 bg-slate-50 text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
        )}
      >
        {isUser ? <div className="whitespace-pre-wrap">{message.content}</div> : <RichText text={message.content} />}
        {!isUser && (
          <div className="mt-2 flex items-center justify-between gap-3 text-xs text-slate-500 dark:text-slate-400">
            <span>{message.confidence !== undefined ? `Confidence: ${Math.round(message.confidence * 100)}%` : "Confidence: n/a"}</span>
            <button onClick={() => onOpenDebug(message.id)} className="underline underline-offset-2">
              Debug
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
