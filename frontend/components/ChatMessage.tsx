import type { ChatMessageData } from "../types";
import SourceCard from "./SourceCard";

export default function ChatMessage({ role, content, sources }: ChatMessageData) {
  const isUser = role === "user";

  return (
    <div className={`flex flex-col gap-2 ${isUser ? "items-end" : "items-start"}`}>
      <div
        className={`max-w-2xl rounded-lg px-4 py-2 text-sm whitespace-pre-wrap ${
          isUser ? "bg-black text-white" : "bg-gray-100 text-gray-900"
        }`}
      >
        {content}
      </div>

      {sources && sources.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {sources.map((s, i) => (
            <SourceCard key={`${s.filePath}-${i}`} {...s} />
          ))}
        </div>
      )}
    </div>
  );
}
