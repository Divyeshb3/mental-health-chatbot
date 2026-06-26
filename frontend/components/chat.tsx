"use client"

import { useEffect, useRef, useState } from "react"
import { Sparkles } from "lucide-react"
import type {ChatMessage } from "@/lib/types"
import { DisclaimerBanner } from "@/components/disclaimer-banner"
import { MessageBubble } from "@/components/message-bubble"
import { TypingIndicator } from "@/components/typing-indicator"
import { ChatInput } from "@/components/chat-input"

const API_URL = "const API_URL = https://mindcare-ai-backend-4wgx.onrender.com"

const SUGGESTIONS = [
  "I've been feeling anxious lately",
  "How can I manage stress?",
  "I'm having trouble sleeping",
]

function createId() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36)
}

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
  }, [messages, isLoading])

  async function handleFeedback(
  message: ChatMessage,
  rating: "positive" | "negative"
) {
  try {
    const assistantIndex = messages.findIndex((m) => m.id === message.id)

    if (assistantIndex <= 0) return

    const question = messages[assistantIndex - 1].content

    const res = await fetch(`${API_URL}/feedback`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    question,
    response: message.content,
    rating,
    sources: message.sources ?? [],
  }),
})

if (!res.ok) {
  throw new Error(`Feedback failed: ${res.status}`)
}

setMessages((prev) =>
  prev.map((m) =>
    m.id === message.id
      ? {
          ...m,
          feedback: rating,
        }
      : m
  )
)

console.log("Feedback submitted")

  } catch (err) {
    console.error("Failed to submit feedback:", err)
  }
}
  async function sendMessage(text: string) {
    const trimmed = text.trim()
    if (!trimmed || isLoading) return

    setError(null)
    setInput("")

    const userMessage: ChatMessage = {
      id: createId(),
      role: "user",
      content: trimmed,
    }

    const conversationHistory = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }))

    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    try {
      const res = await fetch(`${API_URL}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          conversation_history: conversationHistory,
        }),
      })

      if (!res.ok) {
        throw new Error(`Request failed with status ${res.status}`)
      }

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let fullContent = ""
      let sources: string[] = []
      let crisisDetected = false
      const botId = createId()

      // Add empty bot message immediately
      setMessages((prev) => [
        ...prev,
        {
          id: botId,
          role: "assistant",
          content: "",
          sources: [],
          crisisDetected: false,
        },
      ])

      

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const text = decoder.decode(value, { stream: true })
        const lines = text.split("\n").filter((line) => line.startsWith("data: "))

        for (const line of lines) {
          try {
            const data = JSON.parse(line.replace("data: ", ""))

            if (data.type === "sources") {
              sources = data.sources
              crisisDetected = data.crisis_detected
            }

            if (data.type === "crisis") {
              fullContent = data.content
              crisisDetected = true
              sources = []
            }

            if (data.type === "token") {
              fullContent += data.content
            }

            if (data.type === "token" || data.type === "crisis") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === botId
                    ? {
                        ...m,
                        content: fullContent,
                        sources: sources,
                        crisisDetected: crisisDetected,
                      }
                    : m
                )
              )
            }

          } catch {
            // skip malformed lines
          }
        }
      }
    setIsLoading(false)

    } catch (err) {
      console.log("[v0] chat stream failed:", err)
      setError("Couldn't reach the support service. Please check your connection and try again.")
      setIsLoading(false)
    }
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex h-dvh flex-col bg-background">
      <DisclaimerBanner />

      {/* Header */}
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-3">
          <div className="flex size-9 items-center justify-center rounded-full bg-gradient-to-br from-primary to-accent">
            <Sparkles className="size-4 text-primary-foreground" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-foreground">MindCare AI</h1>
            <p className="text-xs text-muted-foreground">
              A safe, judgment-free space to talk
            </p>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-6">
          {isEmpty ? (
            <div className="flex flex-col items-center gap-5 py-10 text-center">
              <div className="flex size-14 items-center justify-center rounded-full bg-gradient-to-br from-primary to-accent">
                <Sparkles className="size-6 text-primary-foreground" aria-hidden="true" />
              </div>
              <div className="space-y-1.5">
                <h2 className="text-balance text-lg font-semibold text-foreground">
                  How are you feeling today?
                </h2>
                <p className="text-pretty text-sm text-muted-foreground">
                  Share whatever is on your mind. I&apos;m here to listen and support you.
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => sendMessage(suggestion)}
                    className="rounded-full border border-border bg-card px-3.5 py-1.5 text-xs text-foreground transition-colors hover:border-primary/60 hover:bg-secondary"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message) => <MessageBubble key={message.id} message={message} onFeedback={handleFeedback} />)
          )}

          {isLoading ? (
            <div className="flex justify-start gap-2.5">
              <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary to-accent">
                <Sparkles className="size-4 text-primary-foreground" aria-hidden="true" />
              </div>
              <TypingIndicator />
            </div>
          ) : null}

          {error ? (
            <p className="text-center text-xs text-destructive" role="status">
              {error}
            </p>
          ) : null}
        </div>
      </div>

      <ChatInput
        value={input}
        onChange={setInput}
        onSend={() => sendMessage(input)}
        disabled={isLoading}
      />
    </div>
  )
}
