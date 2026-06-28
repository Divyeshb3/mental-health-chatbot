"use client"

import { useState } from "react"

const MOODS = [
  { score: 1, emoji: "😢", label: "terrible" },
  { score: 3, emoji: "😟", label: "bad" },
  { score: 5, emoji: "😐", label: "okay" },
  { score: 7, emoji: "🙂", label: "good" },
  { score: 10, emoji: "😊", label: "great" },
]

interface MoodPickerProps {
  onMoodSelected: (score: number, label: string) => void
}

export function MoodPicker({ onMoodSelected }: MoodPickerProps) {
  const [selected, setSelected] = useState<number | null>(null)

  function handleSelect(score: number, label: string) {
    setSelected(score)
    onMoodSelected(score, label)
  }

  return (
    <div className="flex flex-col items-center gap-4 py-6 text-center">
      <p className="text-sm font-medium text-foreground">
        Before we begin, how are you feeling right now?
      </p>
      <div className="flex gap-4">
        {MOODS.map(({ score, emoji, label }) => (
          <button
            key={score}
            onClick={() => handleSelect(score, label)}
            className={`flex flex-col items-center gap-1 rounded-xl p-3 transition-all
              ${selected === score
                ? "bg-primary/20 scale-110 ring-2 ring-primary"
                : "hover:bg-secondary"
              }`}
          >
            <span className="text-2xl">{emoji}</span>
            <span className="text-[10px] text-muted-foreground capitalize">
              {label}
            </span>
          </button>
        ))}
      </div>
      {selected && (
        <p className="text-xs text-muted-foreground">
          Thank you for sharing. I am here to support you.
        </p>
      )}
    </div>
  )
}