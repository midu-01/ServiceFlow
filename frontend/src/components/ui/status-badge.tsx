import * as React from "react";
import { AlertCircle, CheckCircle2, Clock, Loader2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { RequestStatus } from "@/types";

interface StatusBadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  status: RequestStatus;
  showIcon?: boolean;
}

export function StatusBadge({ status, showIcon = true, className, ...props }: StatusBadgeProps) {
  const configs = {
    QUEUED: {
      label: "Queued",
      styles: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
      icon: Clock,
      spin: false,
    },
    PROCESSING: {
      label: "Processing",
      styles: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
      icon: Loader2,
      spin: true,
    },
    COMPLETED: {
      label: "Completed",
      styles: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
      icon: CheckCircle2,
      spin: false,
    },
    FAILED: {
      label: "Failed",
      styles: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20",
      icon: AlertCircle,
      spin: false,
    },
    CANCELLED: {
      label: "Cancelled",
      styles: "bg-slate-500/10 text-slate-600 dark:text-slate-400 border-slate-500/20",
      icon: XCircle,
      spin: false,
    },
  };

  const config = configs[status] || configs.QUEUED;
  const IconComponent = config.icon;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border transition-all",
        config.styles,
        className
      )}
      {...props}
    >
      {showIcon && (
        <IconComponent className={cn("h-3.5 w-3.5", config.spin && "animate-spin")} />
      )}
      <span>{config.label}</span>
    </div>
  );
}
