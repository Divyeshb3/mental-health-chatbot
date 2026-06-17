import { AlertTriangle, Phone } from "lucide-react"

const HELPLINES = [
  { name: "iCall", number: "9152987821" },
  { name: "AASRA", number: "9820466726" },
  { name: "Vandrevala Foundation", number: "9999666555" },
]

interface CrisisAlertProps {
  message: string
}

export function CrisisAlert({ message }: CrisisAlertProps) {
  return (
    <div
      role="alert"
      className="max-w-[85%] rounded-2xl border border-destructive/50 bg-destructive/15 p-4"
    >
      <div className="flex items-center gap-2 text-destructive">
        <AlertTriangle className="size-4 shrink-0" aria-hidden="true" />
        <span className="text-sm font-semibold">You are not alone</span>
      </div>

      {message ? (
        <p className="mt-2 text-pretty text-sm leading-relaxed text-foreground">{message}</p>
      ) : null}

      <p className="mt-3 text-xs font-medium text-muted-foreground">
        Please reach out right now. Help is available 24/7:
      </p>

      <ul className="mt-2 flex flex-col gap-1.5">
        {HELPLINES.map((line) => (
          <li key={line.number}>
            <a
              href={`tel:${line.number}`}
              className="flex items-center gap-2 rounded-lg bg-background/40 px-3 py-2 text-sm transition-colors hover:bg-background/70"
            >
              <Phone className="size-3.5 shrink-0 text-destructive" aria-hidden="true" />
              <span className="font-medium text-foreground">{line.name}</span>
              <span className="ml-auto font-mono text-foreground">{line.number}</span>
            </a>
          </li>
        ))}
      </ul>
    </div>
  )
}
