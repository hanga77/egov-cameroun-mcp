import { cn, formatTime } from "@/lib/utils";
import { ToolExecution } from "./ToolExecution";
import type { Message } from "@/types";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3 animate-slide-up", isUser && "flex-row-reverse")}>
      {/* Avatar */}
      <div
        className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold",
          isUser
            ? "bg-brand-green text-white"
            : "bg-brand-surface border border-brand-border text-brand-yellow"
        )}
      >
        {isUser ? "Vous" : "AI"}
      </div>

      <div className={cn("flex flex-col gap-1 max-w-[80%]", isUser && "items-end")}>
        {/* Bubble */}
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
            isUser
              ? "bg-brand-green text-white rounded-tr-sm"
              : "bg-brand-surface border border-brand-border text-brand-text rounded-tl-sm"
          )}
        >
          {message.content}
        </div>

        {/* Tool executions (assistant only) */}
        {!isUser && message.tool_calls && message.tool_calls.length > 0 && (
          <ToolExecution toolCalls={message.tool_calls} />
        )}

        {/* Timestamp */}
        <span className="text-xs text-brand-text-muted px-1">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
}
