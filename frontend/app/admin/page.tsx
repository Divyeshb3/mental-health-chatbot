"use client"

import { useEffect, useState } from "react"
import { ThumbsUp, ThumbsDown, MessageSquare, Smile, FileText, TrendingUp } from "lucide-react"

const API_URL = "https://mindcare-ai-backend-4wgx.onrender.com"

interface Stats {
  feedback: {
    total: number
    positive: number
    negative: number
    positive_rate: number
  }
  mood: {
    total_entries: number
    average_score: number
    distribution: Record<string, number>
  }
  conversations: {
    total: number
  }
  top_sources: { source: string; count: number }[]
}

const MOOD_EMOJIS: Record<string, string> = {
  terrible: "😢",
  bad: "😟",
  okay: "😐",
  good: "🙂",
  great: "😊"
}

export default function AdminPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchStats()
  }, [])

  async function fetchStats() {
    try {
      const res = await fetch(`${API_URL}/admin/stats`)
      if (!res.ok) throw new Error("Failed to fetch stats")
      const data = await res.json()
      setStats(data)
    } catch (err) {
      setError("Could not load stats. Make sure the backend is running.")
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <p className="text-muted-foreground">Loading dashboard...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <p className="text-red-500">{error}</p>
      </div>
    )
  }

  if (!stats) return null

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-4xl">

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-foreground">MindCare AI — Admin Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">Overview of user interactions and feedback</p>
        </div>

        {/* Top Stats */}
        <div className="grid grid-cols-2 gap-4 mb-6 md:grid-cols-4">
          <StatCard
            icon={<MessageSquare size={20} />}
            label="Total Conversations"
            value={stats.conversations.total}
          />
          <StatCard
            icon={<ThumbsUp size={20} />}
            label="Positive Feedback"
            value={stats.feedback.positive}
            color="text-green-500"
          />
          <StatCard
            icon={<ThumbsDown size={20} />}
            label="Negative Feedback"
            value={stats.feedback.negative}
            color="text-red-500"
          />
          <StatCard
            icon={<Smile size={20} />}
            label="Avg Mood Score"
            value={`${stats.mood.average_score}/10`}
            color="text-purple-500"
          />
        </div>

        {/* Feedback Rate */}
        <div className="mb-6 rounded-xl border border-border bg-card p-5">
          <h2 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <TrendingUp size={16} /> Feedback Satisfaction Rate
          </h2>
          <div className="flex items-center gap-3">
            <div className="flex-1 h-3 rounded-full bg-secondary overflow-hidden">
              <div
                className="h-full rounded-full bg-green-500 transition-all"
                style={{ width: `${stats.feedback.positive_rate}%` }}
              />
            </div>
            <span className="text-sm font-medium text-foreground">
              {stats.feedback.positive_rate}%
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            {stats.feedback.positive} positive out of {stats.feedback.total} total ratings
          </p>
        </div>

        {/* Mood Distribution */}
        <div className="mb-6 rounded-xl border border-border bg-card p-5">
          <h2 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <Smile size={16} /> Mood Distribution
          </h2>
          <div className="flex justify-around">
            {Object.entries(stats.mood.distribution).map(([label, count]) => (
              <div key={label} className="flex flex-col items-center gap-1">
                <span className="text-2xl">{MOOD_EMOJIS[label] || "😐"}</span>
                <span className="text-xs text-muted-foreground capitalize">{label}</span>
                <span className="text-sm font-semibold text-foreground">{count}</span>
              </div>
            ))}
            {Object.keys(stats.mood.distribution).length === 0 && (
              <p className="text-xs text-muted-foreground">No mood data yet</p>
            )}
          </div>
        </div>

        {/* Top Sources */}
        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <FileText size={16} /> Most Cited Sources
          </h2>
          <div className="flex flex-col gap-3">
            {stats.top_sources.length === 0 ? (
              <p className="text-xs text-muted-foreground">No source data yet</p>
            ) : (
              stats.top_sources.map(({ source, count }) => (
                <div key={source} className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground truncate flex-1">{source}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2 rounded-full bg-secondary overflow-hidden">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{
                          width: `${(count / (stats.top_sources[0]?.count || 1)) * 100}%`
                        }}
                      />
                    </div>
                    <span className="text-xs font-medium text-foreground w-4">{count}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  )
}

function StatCard({
  icon,
  label,
  value,
  color = "text-primary"
}: {
  icon: React.ReactNode
  label: string
  value: string | number
  color?: string
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className={`mb-2 ${color}`}>{icon}</div>
      <p className="text-xl font-bold text-foreground">{value}</p>
      <p className="text-xs text-muted-foreground mt-0.5">{label}</p>
    </div>
  )
}