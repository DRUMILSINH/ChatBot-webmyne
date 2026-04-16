type NewChatButtonProps = {
  onClick: () => void;
};

export function NewChatButton({ onClick }: NewChatButtonProps) {
  return (
    <button
      onClick={onClick}
      className="w-full rounded-lg bg-brand-600 px-3 py-2 text-sm font-semibold text-white hover:bg-brand-700"
    >
      New Chat
    </button>
  );
}
