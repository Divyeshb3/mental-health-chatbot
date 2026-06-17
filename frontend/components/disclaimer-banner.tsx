import { Info } from "lucide-react"

export function DisclaimerBanner() {
  return (
    <div className="sticky top-0 z-20 border-b border-border bg-secondary/80 backdrop-blur">
      <div className="mx-auto flex max-w-3xl items-start gap-2 px-4 py-2.5">
        <Info className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden="true" />
        <p className="text-pretty text-xs leading-relaxed text-muted-foreground">
          This chatbot is not a substitute for professional help. In crisis? Call{" "}
          <a
            href="tel:9152987821"
            className="font-medium text-foreground underline underline-offset-2 hover:text-primary"
          >
            iCall: 9152987821
          </a>
        </p>
      </div>
    </div>
  )
}
