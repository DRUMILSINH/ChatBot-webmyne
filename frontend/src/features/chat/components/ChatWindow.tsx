import { ChatMessage } from '../types';
import { Composer } from './Composer';
import { MessageList } from './MessageList';

type ChatWindowProps = {
  messages: ChatMessage[];
  streamBuffer: string;
  isStreaming: boolean;
  onSend: (query: string) => Promise<void>;
  onOpenDebug: (messageId: number) => void;
};

export function ChatWindow({ messages, streamBuffer, isStreaming, onSend, onOpenDebug }: ChatWindowProps) {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <MessageList messages={messages} streamingContent={streamBuffer} onOpenDebug={onOpenDebug} />
      <Composer disabled={isStreaming} onSend={onSend} />
    </div>
  );
}
