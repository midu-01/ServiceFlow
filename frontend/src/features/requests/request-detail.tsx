"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  ArrowLeft,
  Ban,
  Calendar,
  Check,
  Clock,
  Copy,
  Layers,
  Loader2,
  RefreshCw,
  User,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { CancelDialog } from "@/features/requests/cancel-dialog";
import { apiClient, ApiClientError } from "@/lib/api/client";
import { requestKeys } from "@/lib/api/query-keys";
import { ApiResponse, ServiceRequest } from "@/types";
import { cn } from "@/lib/utils";

interface RequestDetailProps {
  requestId: string;
}

export function RequestDetail({ requestId }: RequestDetailProps) {
  const queryClient = useQueryClient();
  const [copied, setCopied] = useState(false);
  const [cancelOpen, setCancelOpen] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: requestKeys.detail(requestId),
    queryFn: () => apiClient<ApiResponse<ServiceRequest>>(`/api/v1/service-requests/${requestId}`),
    staleTime: 1000 * 3, // 3 seconds
  });

  const sr = data?.data;

  const copyId = () => {
    if (typeof window !== "undefined") {
      navigator.clipboard.writeText(requestId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleCancelConfirm = async () => {
    setIsCancelling(true);
    setCancelError(null);

    try {
      await apiClient(`/api/v1/service-requests/${requestId}/cancel`, {
        method: "POST",
      });
      await queryClient.invalidateQueries({ queryKey: requestKeys.all });
      setCancelOpen(false);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setCancelError(err.message);
      } else {
        setCancelError("Failed to cancel request. Please try again.");
      }
    } finally {
      setIsCancelling(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-16 text-center rounded-2xl border border-border bg-card space-y-3 max-w-3xl mx-auto my-8">
        <Loader2 className="h-8 w-8 text-blue-600 animate-spin mx-auto" />
        <p className="text-xs text-muted-foreground">Loading service request details...</p>
      </div>
    );
  }

  if (isError || !sr) {
    const errorMsg =
      error instanceof ApiClientError ? error.message : "Service request not found or access denied.";
    return (
      <div className="max-w-2xl mx-auto my-8 space-y-4">
        <Alert variant="destructive">
          <AlertCircle className="h-5 w-5" />
          <AlertTitle>Unable to Load Request</AlertTitle>
          <AlertDescription>{errorMsg}</AlertDescription>
        </Alert>
        <Link href="/requests">
          <Button variant="outline" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Requests
          </Button>
        </Link>
      </div>
    );
  }

  const isCancellable = sr.status === "QUEUED";

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Cancellation Modal */}
      <CancelDialog
        open={cancelOpen}
        onOpenChange={setCancelOpen}
        requestTitle={sr.title}
        isCancelling={isCancelling}
        onConfirm={handleCancelConfirm}
      />

      {/* Top Navigation & Status Bar */}
      <div className="flex items-center justify-between">
        <Link href="/requests">
          <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-muted-foreground">
            <ArrowLeft className="h-4 w-4" />
            Back to Queue
          </Button>
        </Link>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            className="gap-1.5 text-xs"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", isFetching && "animate-spin")} />
            <span>Refresh</span>
          </Button>

          {isCancellable && (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setCancelOpen(true)}
              className="gap-1.5 text-xs"
            >
              <Ban className="h-3.5 w-3.5" />
              Cancel Request
            </Button>
          )}
        </div>
      </div>

      {cancelError && (
        <Alert variant="destructive">
          <AlertTitle>Cancellation Conflict</AlertTitle>
          <AlertDescription>{cancelError}</AlertDescription>
        </Alert>
      )}

      {/* Main Request Information Card */}
      <Card className="border-border shadow-sm overflow-hidden">
        <CardHeader className="space-y-3 pb-6 border-b border-border bg-slate-50/50 dark:bg-slate-900/30">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <StatusBadge status={sr.status} className="self-start text-xs px-3 py-1" />
            <button
              onClick={copyId}
              className="inline-flex items-center gap-1.5 text-[11px] font-mono text-muted-foreground opacity-70 hover:opacity-100 hover:text-foreground transition-opacity"
              title="Copy UUID to clipboard"
            >
              <span>{sr.id}</span>
              {copied ? <Check className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3" />}
            </button>
          </div>

          <h2 className="text-xl font-bold tracking-tight text-foreground">{sr.title}</h2>
        </CardHeader>

        <CardContent className="space-y-6 pt-6">
          {/* Progress Section */}
          <div className="p-4 rounded-xl border border-border bg-card space-y-3">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold uppercase tracking-wider text-muted-foreground">
                Execution Progress
              </span>
              <span className="font-bold text-sm text-foreground">{sr.progress_percent}%</span>
            </div>

            <Progress
              value={sr.progress_percent}
              statusVariant={
                sr.status === "FAILED"
                  ? "error"
                  : sr.status === "COMPLETED"
                  ? "success"
                  : "default"
              }
              className="h-3"
            />

            <div className="text-xs text-muted-foreground flex items-center gap-1.5">
              <span className="opacity-70">Current Step:</span>
              <span className="font-medium text-foreground">
                {sr.current_step || (sr.status === "QUEUED" ? "Awaiting worker pickup" : "Finished")}
              </span>
            </div>
          </div>

          {/* Failure Alert Banner */}
          {sr.status === "FAILED" && sr.error_message && (
            <Alert variant="destructive">
              <AlertTitle>Worker Processing Failed</AlertTitle>
              <AlertDescription>{sr.error_message}</AlertDescription>
            </Alert>
          )}

          {/* Request Description */}
          <div className="space-y-1.5">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Workload Description
            </h4>
            <p className="text-sm leading-relaxed whitespace-pre-wrap p-4 rounded-xl border border-border bg-slate-50/50 dark:bg-slate-900/30">
              {sr.description}
            </p>
          </div>

          {/* Milestone Timestamps Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-border text-xs">
            <div className="p-3 rounded-lg bg-background border border-border space-y-1">
              <span className="text-[10px] uppercase font-semibold text-muted-foreground opacity-70 block">
                Submitted
              </span>
              <span className="font-medium text-foreground block">
                {new Date(sr.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </span>
              <span className="text-[10px] text-muted-foreground opacity-60 block">
                {new Date(sr.created_at).toLocaleDateString([], { month: "short", day: "numeric" })}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-background border border-border space-y-1">
              <span className="text-[10px] uppercase font-semibold text-muted-foreground opacity-70 block">
                Started
              </span>
              <span className="font-medium text-foreground block">
                {sr.started_at
                  ? new Date(sr.started_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                  : "Pending"}
              </span>
              {sr.started_at && (
                <span className="text-[10px] text-muted-foreground opacity-60 block">
                  {new Date(sr.started_at).toLocaleDateString([], { month: "short", day: "numeric" })}
                </span>
              )}
            </div>

            <div className="p-3 rounded-lg bg-background border border-border space-y-1">
              <span className="text-[10px] uppercase font-semibold text-muted-foreground opacity-70 block">
                Completed
              </span>
              <span className="font-medium text-foreground block">
                {sr.completed_at
                  ? new Date(sr.completed_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                  : "Pending"}
              </span>
              {sr.completed_at && (
                <span className="text-[10px] text-muted-foreground opacity-60 block">
                  {new Date(sr.completed_at).toLocaleDateString([], { month: "short", day: "numeric" })}
                </span>
              )}
            </div>

            <div className="p-3 rounded-lg bg-background border border-border space-y-1">
              <span className="text-[10px] uppercase font-semibold text-muted-foreground opacity-70 block">
                Cancelled
              </span>
              <span className="font-medium text-foreground block">
                {sr.cancelled_at
                  ? new Date(sr.cancelled_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                  : "N/A"}
              </span>
              {sr.cancelled_at && (
                <span className="text-[10px] text-muted-foreground opacity-60 block">
                  {new Date(sr.cancelled_at).toLocaleDateString([], { month: "short", day: "numeric" })}
                </span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
