export type Role = "user" | "assistant"

export interface ChatMessage {
  id: string
  role: Role
  content: string
  sources?: string[]
  crisisDetected?: boolean
}

// Shape sent to / received from the backend API.
export interface ChatApiRequest {
  message: string
  conversation_history: { role: Role; content: string }[]
}

export interface ChatApiResponse {
  response: string
  sources: string[]
  crisis_detected: boolean
}
