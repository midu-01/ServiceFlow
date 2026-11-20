"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowRight,
  Ban,
  Clock,
  Filter,
  Inbox,
  Loader2,
  PlusCircle,
  RefreshCw,
  Search,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/ui/status-badge";
import { Progress } from "@/components/ui/progress";
import { Card } from "@/components/ui/card";
import { CancelDialog } from "@/features/requests/cancel-dialog";
import { apiClient, ApiClientError } from "@/lib/api/client";
import { requestKeys } from "@/lib/api/query-keys";
import { PaginatedResponse, RequestStatus, ServiceRequest } from "@/types";
import { cn } from "@/lib/utils";

const STATUS_FILTERS: Array<{ label: string; value: RequestStatus | "ALL" }> = [
  { label: "All Statuses", value: "ALL" },
  { label: "Queued", value: "QUEUED" },
  { label: "Processing", value: "PROCESSING" },
  { label: "Completed", value: "COMPLETED" },
  { label: "Failed", value: "FAILED" },
  { label: "Cancelled", value: "CANCELLED" },
];

export function RequestList() {
  const queryClient = useQueryClient();
  const [selectedStatus, setSelectedStatus] = useState<RequestStatus | "ALL">("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [page, setPage] = useState<number>(1);
  const pageSize = 15;

  // Cancellation modal state
  const [cancelTarget, setCancelTarget] = useState<ServiceRequest | null>(null);
  const [isCancelling, setIsCancelling] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const queryParams = {
    status: selectedStatus === "ALL" ? undefined : selectedStatus,
    search: searchQuery.trim() || undefined,
    limit: pageSize,
    offset: (page - 1) * pageSize,
  };

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: requestKeys.list(queryParams),
    queryFn: () => {
      const sp = new URLSearchParams();
      if (queryParams.status) sp.set("status", queryParams.status);
      if (queryParams.search) sp.set("search", queryParams.search);
      sp.set("limit", String(queryParams.limit));
      sp.set("offset", String(queryParams.offset));

      return apiClient<PaginatedResponse<ServiceRequest>>(`/api/v1/service-requests?${sp.toString()}`);
    },
    staleTime: 1000 * 5, // 5 seconds
  });

  const requests = data?.data || [];
  const meta = data?.meta || { total: 0, limit: pageSize, offset: 0, total_pages: 1, current_page: 1 };

  const handleCancelConfirm = async () => {
    if (!cancelTarget) return;
    setIsCancelling(true);
    setActionError(null);

    try {
      await apiClient(`/api/v1/service-requests/${cancelTarget.id}/cancel`, {
        method: "POST",
      });
      await queryClient.invalidateQueries({ queryKey: requestKeys.all });
      setCancelTarget(null);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setActionError(err.message);
      } else {
        setActionError("Failed to cancel request.");
      }
    } finally {
      setIsCancelling(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Cancellation Modal */}
      {cancelTarget && (
        <CancelDialog
          open={!!cancelTarget}
          onOpenChange={(open) => !open && setCancelTarget(null)}
          requestTitle={cancelTarget.title}
          isCancelling={isCancelling}
          onConfirm={handleCancelConfirm}
        />
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
        {/* Search Input */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground opacity-50" />
          <Input
            type="text"
            placeholder="Search by title or description..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPage(1);
            }}
            className="pl-9 pr-9"
          />
          {searchQuery && (
            <button
              onClick={() => {
                setSearchQuery("");
                setPage(1);
              }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground opacity-50 hover:opacity-100"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Action Button & Manual Refresh */}
        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            className="gap-1.5"
            title="Refresh request queue"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", isFetching && "animate-spin")} />
            <span className="hidden sm:inline">Refresh</span>
          </Button>

          <Link href="/requests/new">
            <Button size="sm" className="gap-1.5">
              <PlusCircle className="h-4 w-4" />
              <span>New Request</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-border text-sm">
        <Filter className="h-4 w-4 text-muted-foreground opacity-60 mr-1 shrink-0" />
        {STATUS_FILTERS.map((tab) => {
          const isSelected = selectedStatus === tab.value;
          return (
            <button
              key={tab.value}
              onClick={() => {
                setSelectedStatus(tab.value);
                setPage(1);
              }}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors",
                isSelected
                  ? "bg-blue-600 text-white font-semibold shadow-sm"
                  : "text-muted-foreground opacity-75 hover:opacity-100 hover:bg-slate-100 dark:hover:bg-slate-800"
              )}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {actionError && (
        <div className="p-3 rounded-lg bg-rose-500/10 text-rose-600 border border-rose-500/20 text-xs font-medium">
          {actionError}
        </div>
      )}

      {/* Table & Card Presentation */}
      {isLoading ? (
        <div className="p-12 text-center rounded-2xl border border-border bg-card space-y-3">
          <Loader2 className="h-8 w-8 text-blue-600 animate-spin mx-auto" />
          <p className="text-xs text-muted-foreground">Fetching service requests from queue...</p>
        </div>
      ) : requests.length === 0 ? (
        <div className="p-16 text-center rounded-2xl border border-dashed border-border bg-card/50 space-y-4">
          <div className="h-12 w-12 rounded-full bg-slate-100 dark:bg-slate-800 text-muted-foreground flex items-center justify-center mx-auto">
            <Inbox className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <h3 className="font-semibold text-base">No service requests found</h3>
            <p className="text-xs text-muted-foreground opacity-75 max-w-sm mx-auto">
              {searchQuery || selectedStatus !== "ALL"
                ? "No requests match the active filter criteria. Try resetting your search."
                : "The queue is currently empty. Submit your first request to begin processing."}
            </p>
          </div>
          {searchQuery || selectedStatus !== "ALL" ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSelectedStatus("ALL");
                setSearchQuery("");
              }}
            >
              Clear Filters
            </Button>
          ) : (
            <Link href="/requests/new">
              <Button size="sm" className="gap-1.5">
                <PlusCircle className="h-4 w-4" />
                Submit Request
              </Button>
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          <Card className="overflow-hidden border-border shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 dark:bg-slate-900/60 border-b border-border text-[11px] uppercase tracking-wider text-muted-foreground font-semibold">
                  <tr>
                    <th className="py-3 px-4">Request</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 w-48">Progress</th>
                    <th className="py-3 px-4">Created</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {requests.map((req) => {
                    const isCancellable = req.status === "QUEUED";
                    const formattedDate = new Date(req.created_at).toLocaleString(undefined, {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    });

                    return (
                      <tr key={req.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/40 transition-colors">
                        <td className="py-3.5 px-4 max-w-xs sm:max-w-md">
                          <Link
                            href={`/requests/${req.id}`}
                            className="font-medium hover:text-blue-600 transition-colors line-clamp-1"
                          >
                            {req.title}
                          </Link>
                          <p className="text-xs text-muted-foreground opacity-70 line-clamp-1 mt-0.5">
                            {req.description}
                          </p>
                        </td>

                        <td className="py-3.5 px-4 whitespace-nowrap">
                          <StatusBadge status={req.status} />
                        </td>

                        <td className="py-3.5 px-4">
                          <div className="space-y-1">
                            <Progress
                              value={req.progress_percent}
                              statusVariant={
                                req.status === "FAILED"
                                  ? "error"
                                  : req.status === "COMPLETED"
                                  ? "success"
                                  : "default"
                              }
                            />
                            {req.current_step && (
                              <p className="text-[10px] text-muted-foreground opacity-70 truncate">
                                {req.current_step}
                              </p>
                            )}
                          </div>
                        </td>

                        <td className="py-3.5 px-4 text-xs text-muted-foreground whitespace-nowrap">
                          {formattedDate}
                        </td>

                        <td className="py-3.5 px-4 text-right whitespace-nowrap">
                          <div className="flex items-center justify-end gap-1.5">
                            {isCancellable && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setCancelTarget(req)}
                                className="text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/30 h-8 px-2.5"
                                title="Cancel queued request"
                              >
                                <Ban className="h-3.5 w-3.5 mr-1" />
                                Cancel
                              </Button>
                            )}

                            <Link href={`/requests/${req.id}`}>
                              <Button variant="outline" size="sm" className="h-8 px-2.5 text-xs gap-1">
                                <span>Details</span>
                                <ArrowRight className="h-3 w-3" />
                              </Button>
                            </Link>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Pagination Navigation */}
          {meta.total_pages > 1 && (
            <div className="flex items-center justify-between text-xs text-muted-foreground px-2 pt-2">
              <div>
                Showing <span className="font-semibold text-foreground">{requests.length}</span> of{" "}
                <span className="font-semibold text-foreground">{meta.total}</span> requests
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                >
                  Previous
                </Button>
                <span className="px-2 font-medium">
                  Page {meta.current_page} of {meta.total_pages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(meta.total_pages, p + 1))}
                  disabled={page >= meta.total_pages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
