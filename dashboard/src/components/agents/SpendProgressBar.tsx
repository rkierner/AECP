import { cn } from "@/lib/utils";
import { formatCurrency } from "@/lib/formatters";

interface SpendProgressBarProps {
  current: number;
  budget: number;
}

export function SpendProgressBar({ current, budget }: SpendProgressBarProps) {
  const pct = budget > 0 ? Math.min((current / budget) * 100, 100) : 0;
  const isWarning = pct >= 80;
  const isCritical = pct >= 95;

  return (
    <div className="min-w-[120px]">
      <div className="flex justify-between text-xs text-muted-foreground mb-1">
        <span className="font-medium text-foreground">{formatCurrency(current)}</span>
        <span>{formatCurrency(budget)}</span>
      </div>
      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full transition-all",
            isCritical
              ? "bg-red-500"
              : isWarning
              ? "bg-yellow-500"
              : "bg-blue-500"
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
