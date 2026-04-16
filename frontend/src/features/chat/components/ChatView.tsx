import { ChatMessage, DebugPayload } from "../types";
import { ChatWindow } from "./ChatWindow";
import { DebugDrawer } from "./DebugDrawer";

type ChatViewProps = {
  messages: ChatMessage[];
  streamBuffer: string;
  isStreaming: boolean;
  onSend: (query: string) => Promise<void>;
  onOpenDebug: (messageId: number) => void;
  debug: DebugPayload | null;
  selectedMessageId: number | null;
};

export function ChatView({
  messages,
  streamBuffer,
  isStreaming,
  onSend,
  onOpenDebug,
  debug,
  selectedMessageId,
}: ChatViewProps) {
  return (
    <>
      <div className="flex min-h-0 flex-1">
        <section className="flex min-w-0 flex-1 flex-col">
          <ChatWindow
            messages={messages}
            streamBuffer={streamBuffer}
            isStreaming={isStreaming}
            onSend={onSend}
            onOpenDebug={onOpenDebug}
          />
        </section>
        <aside className="hidden w-[360px] shrink-0 border-l border-slate-200 bg-slate-50/60 dark:border-slate-800 dark:bg-slate-900/50 xl:block">
          <DebugDrawer debug={debug} selectedMessageId={selectedMessageId} />
        </aside>
      </div>
      <details className="border-t border-slate-200 p-2 xl:hidden dark:border-slate-800">
        <summary className="cursor-pointer text-sm font-medium">Debug Drawer</summary>
        <div className="mt-2 max-h-80 overflow-y-auto">
          <DebugDrawer debug={debug} selectedMessageId={selectedMessageId} />
        </div>
      </details>
    </>
  );
}
