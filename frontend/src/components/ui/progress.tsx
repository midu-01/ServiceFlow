import * as React from "react";
import { cn } from "@/lib/utils";

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number; // 0 to 100
  showLabel?: boolean;
  statusVariant?: "default" | "success" | "error";
}

export function Progress({
  value,
  showLabel = false,
  statusVariant = "default",
  className,
  ...props
}: ProgressProps) {
  const clampedValue = Math.min(100, Math.max(0, value));

  const barColors = {
    default: "bg-blue-600",
    success: "bg-emerald-500",
    error: "bg-rose-500",
  };

  return (
    <div className={cn("w-full space-y-1.5", className)} {...props}>
      <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
        <div
          className={cn(
            "h-full transition-all duration-500 ease-out rounded-full",
            barColors[statusVariant]
          )}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
      {showLabel && (
        <div className="flex justify-between items-center text-xs text-muted-foreground opacity-75">
          <span>Progress</span>
          <span className="font-semibold">{clampedValue}%</span>
        </div>
      )}
    </div>
  );
}
