"use client"

import { useEffect, useState } from "react"
import { MessageSquare, X, Menu } from "lucide-react"

interface Session {
  session_id: string
  updated_at: string
  preview: string
}

interface SessionSidebarProps {
  apiUrl: string
  onSelectSession: (sessionId: string) => void
  currentSessionId: string
}

export function SessionSidebar({ apiUrl, onSelectSession, currentSessionId }: SessionSidebarProps) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    fetchSessions()
  }, [currentSessionId])

  async function fetchSessions() {
    try {
      const res = await fetch(`${apiUrl}/conversations/recent`)
      const data = await res.json()
      setSessions(data.sessions || [])
    } catch (err) {
      console.log("Failed to fetch sessions:", err)
    }
  }

  return (
    <>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed left-4 top-4 z-50 rounded-full bg-card p-2 border border-border"
      >
        {isOpen ? <X size={18} /> : <Menu size={18} />}
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-40 bg-black/50" onClick={() => setIsOpen(false)} />
      )}

      <div
        className={`fixed left-0 top-0 z-40 h-full w-72 transform bg-card border-r border-border transition-transform ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="p-4 pt-16">
          <h2 className="text-sm font-semibold mb-3">Past Conversations</h2>
          <div className="flex flex-col gap-2">
            {sessions.length === 0 ? (
              <p className="text-xs text-muted-foreground">No past conversations yet</p>
            ) : (
              sessions.map((session) => (
                <button
                  key={session.session_id}
                  onClick={() => {
                    onSelectSession(session.session_id)
                    setIsOpen(false)
                  }}
                  className={`flex items-start gap-2 rounded-lg p-2.5 text-left text-xs hover:bg-secondary ${
                    session.session_id === currentSessionId ? "bg-secondary" : ""
                  }`}
                >
                  <MessageSquare size={14} className="mt-0.5 shrink-0 text-muted-foreground" />
                  <span className="line-clamp-2 text-muted-foreground">
                    {session.preview || "New conversation"}
                  </span>
                </button>
              ))
            )}
          </div>
        </div>
      </div>
    </>
  )
}