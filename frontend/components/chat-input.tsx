"use client"

import { useRef, type FormEvent, type KeyboardEvent } from "react"
import { SendHorizontal } from "lucide-react"

interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  disabled?: boolean
}

export function ChatInput({ value, onChange, onSend, disabled }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (disabled || !value.trim()) return
    onSend()
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      if (disabled || !value.trim()) return
      onSend()
    }
  }

  return (
    <div className="sticky bottom-0 border-t border-border bg-background/80 backdrop-blur">
      <form
        onSubmit={handleSubmit}
        className="mx-auto flex max-w-3xl items-end gap-2 px-4 py-3"
      >
        <div className="flex flex-1 items-end rounded-2xl border border-border bg-card px-3 py-2 focus-within:border-primary/60 focus-within:ring-1 focus-within:ring-primary/40">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            placeholder="Share what's on your mind..."
            aria-label="Message"
            className="max-h-32 w-full resize-none bg-transparent text-sm leading-relaxed text-foreground outline-none placeholder:text-muted-foreground"
          />
        </div>
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          aria-label="Send message"
          className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-primary text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <SendHorizontal className="size-5" aria-hidden="true" />
        </button>
      </form>
    </div>
  )
}
