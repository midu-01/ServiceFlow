"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Clock,
  Layers,
  Loader2,
  PlusCircle,
  Radio,
  Shield,
  Zap,
} from "lucide-react";
import { ProtectedRoute } from "@/components/auth/protected-route";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/ui/status-badge";
import { Progress } from "@/components/ui/progress";
import { useAuth } from "@/hooks/use-auth";
import { useWebSocket } from "@/hooks/use-websocket";
import { apiClient } from "@/lib/api/client";
import { requestKeys } from "@/lib/api/query-keys";
import { PaginatedResponse, ServiceRequest } from "@/types";

export default function DashboardPage() {
  const { user } = useAuth();
  const { status: wsStatus, recentEvents } = useWebSocket();

  // Query up to 100 recent requests for live metrics
  const { data } = useQuery({
    queryKey: requestKeys.list({ limit: 100 }),
    queryFn: () => apiClient<PaginatedResponse<ServiceRequest>>("/api/v1/service-requests?limit=100"),
    staleTime: 1000 * 10,
  });

  if (!user) return null;

  const isOperator = user.role === "OPERATOR";
  const requests = data?.data || [];

  // Metrics computation
  const queuedCount = requests.filter((r) => r.status === "QUEUED").length;
  const processingRequests = requests.filter((r) => r.status === "PROCESSING");
  const completedCount = requests.filter((r) => r.status === "COMPLETED").length;
  const failedCount = requests.filter((r) => r.status === "FAILED").length;

  return (
    <ProtectedRoute>
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Welcome Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-blue-600/10 via-indigo-600/5 to-transparent border border-border">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight">
                Welcome back, {user.username}
              </h1>
              <Badge variant="secondary" className="text-xs uppercase font-bold tracking-wider">
                {user.role}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground opacity-80">
              ServiceFlow Operations Console &bull; Real-time push updates active
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/requests">
              <Button variant="outline" size="sm">
                View Queue
              </Button>
            </Link>
            <Link href="/requests/new">
              <Button size="sm" className="gap-2">
                <PlusCircle className="h-4 w-4" />
                New Request
              </Button>
            </Link>
          </div>
        </div>

        {/* Live Metrics Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl border border-border bg-card shadow-sm space-y-2">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-semibold uppercase tracking-wider">Queued</span>
              <Clock className="h-4 w-4 text-amber-500" />
            </div>
            <div className="text-2xl font-bold tracking-tight text-foreground">{queuedCount}</div>
            <div className="text-[11px] text-muted-foreground opacity-70">Awaiting worker pickup</div>
          </div>

          <div className="p-4 rounded-xl border border-border bg-card shadow-sm space-y-2">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-semibold uppercase tracking-wider">In Processing</span>
              <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
            </div>
            <div className="text-2xl font-bold tracking-tight text-blue-600">
              {processingRequests.length}
            </div>
            <div className="text-[11px] text-muted-foreground opacity-70">Active background tasks</div>
          </div>

          <div className="p-4 rounded-xl border border-border bg-card shadow-sm space-y-2">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-semibold uppercase tracking-wider">Completed</span>
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            </div>
            <div className="text-2xl font-bold tracking-tight text-emerald-600">{completedCount}</div>
            <div className="text-[11px] text-muted-foreground opacity-70">Processed successfully</div>
          </div>

          <div className="p-4 rounded-xl border border-border bg-card shadow-sm space-y-2">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-semibold uppercase tracking-wider">Failed</span>
              <AlertCircle className="h-4 w-4 text-rose-500" />
            </div>
            <div className="text-2xl font-bold tracking-tight text-rose-600">{failedCount}</div>
            <div className="text-[11px] text-muted-foreground opacity-70">Encountered errors</div>
          </div>
        </div>

        {/* Live Active Workloads Stream */}
        <Card className="border-border shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-blue-600" />
                <CardTitle className="text-base font-semibold">Active Background Workloads</CardTitle>
              </div>
              <CardDescription>
                Real-time progress streaming directly from Celery worker threads via WebSockets.
              </CardDescription>
            </div>
            <span className="text-xs font-medium px-2 py-1 rounded-md bg-blue-500/10 text-blue-600">
              {processingRequests.length} Running
            </span>
          </CardHeader>
          <CardContent>
            {processingRequests.length === 0 ? (
              <div className="py-8 text-center text-xs text-muted-foreground opacity-75 border border-dashed border-border rounded-xl">
                No requests currently in processing. Submit a new workload to watch live progress.
              </div>
            ) : (
              <div className="space-y-4">
                {processingRequests.map((req) => (
                  <div
                    key={req.id}
                    className="p-4 rounded-xl border border-border bg-slate-50/50 dark:bg-slate-900/40 space-y-2.5 transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <Link
                        href={`/requests/${req.id}`}
                        className="font-medium text-sm hover:text-blue-600 transition-colors line-clamp-1"
                      >
                        {req.title}
                      </Link>
                      <span className="text-xs font-bold text-blue-600">{req.progress_percent}%</span>
                    </div>

                    <Progress value={req.progress_percent} statusVariant="default" />

                    <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                      <span className="truncate">{req.current_step || "Executing pipeline..."}</span>
                      <Link
                        href={`/requests/${req.id}`}
                        className="text-blue-600 hover:underline shrink-0 ml-2"
                      >
                        View Details &rarr;
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Real-Time Events Feed */}
        <Card className="border-border shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Radio className="h-4 w-4 text-emerald-500 animate-pulse" />
                <CardTitle className="text-base font-semibold">Live Event Stream</CardTitle>
              </div>
              <Badge variant="outline" className="text-[11px]">
                {wsStatus === "connected" ? "Listening" : wsStatus}
              </Badge>
            </div>
            <CardDescription>
              Discrete event envelopes broadcasted by background workers across Redis Pub/Sub.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {recentEvents.length === 0 ? (
              <div className="py-8 text-center text-xs text-muted-foreground opacity-75 border border-dashed border-border rounded-xl">
                Awaiting incoming WebSocket events... Create or cancel a request to stream updates.
              </div>
            ) : (
              <div className="divide-y divide-border text-xs max-h-64 overflow-y-auto">
                {recentEvents.map((evt) => (
                  <div key={evt.event_id} className="py-2.5 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5 truncate">
                      <span className="font-mono text-[10px] text-muted-foreground opacity-60 shrink-0">
                        {new Date(evt.occurred_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                      </span>
                      <Badge variant="secondary" className="text-[10px] font-mono shrink-0">
                        {evt.event_type}
                      </Badge>
                      <span className="truncate text-foreground font-medium">
                        Request ID: {evt.request_id ? `${evt.request_id.slice(0, 8)}...` : "System"}
                      </span>
                    </div>

                    <div className="text-[11px] text-muted-foreground shrink-0 font-medium">
                      {(evt.data as any)?.status || `${(evt.data as any)?.progress_percent ?? ""}%`}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}
