import { Sparkles } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ChatMessage } from "@/lib/types"
import { CrisisAlert } from "@/components/crisis-alert"

interface MessageBubbleProps {
  message: ChatMessage
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user"

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-sm leading-relaxed text-primary-foreground">
          <p className="text-pretty whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start gap-2.5">
      <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary to-accent">
        <Sparkles className="size-4 text-primary-foreground" aria-hidden="true" />
      </div>

      <div className="flex max-w-[85%] flex-col gap-2">
        {message.crisisDetected ? (
          <CrisisAlert message={message.content} />
        ) : (
          <div className="rounded-2xl rounded-bl-md border border-border bg-card px-4 py-2.5 text-sm leading-relaxed text-card-foreground">
            <p className="text-pretty whitespace-pre-wrap">{message.content}</p>
          </div>
        )}

        {message.sources && message.sources.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {message.sources.map((source, index) => (
              <span
                key={`${source}-${index}`}
                className={cn(
                  "inline-flex items-center rounded-full border border-border bg-secondary px-2.5 py-0.5",
                  "text-[11px] font-medium text-muted-foreground",
                )}
              >
                {source}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  )
}
