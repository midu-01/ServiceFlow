import * as React from "react";
import { AlertCircle, AlertTriangle, CheckCircle2, Info } from "lucide-react";
import { cn } from "@/lib/utils";

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "success" | "warning" | "destructive";
}

const alertVariants = {
  default: "bg-blue-500/10 text-blue-800 dark:text-blue-300 border-blue-500/20",
  success: "bg-emerald-500/10 text-emerald-800 dark:text-emerald-300 border-emerald-500/20",
  warning: "bg-amber-500/10 text-amber-800 dark:text-amber-300 border-amber-500/20",
  destructive: "bg-rose-500/10 text-rose-800 dark:text-rose-300 border-rose-500/20",
};

const alertIcons = {
  default: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  destructive: AlertCircle,
};

export function Alert({ variant = "default", className, children, ...props }: AlertProps) {
  const IconComponent = alertIcons[variant];

  return (
    <div
      role="alert"
      className={cn(
        "relative w-full rounded-xl border p-4 text-sm flex items-start gap-3 transition-colors",
        alertVariants[variant],
        className
      )}
      {...props}
    >
      <IconComponent className="h-5 w-5 shrink-0 mt-0.5" />
      <div className="flex-1 space-y-1">{children}</div>
    </div>
  );
}

export function AlertTitle({ className, children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h5 className={cn("font-semibold leading-none tracking-tight", className)} {...props}>
      {children}
    </h5>
  );
}

export function AlertDescription({ className, children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <div className={cn("text-xs leading-relaxed opacity-90", className)} {...props}>
      {children}
    </div>
  );
}
