import Link from "next/link";
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Cpu,
  Layers,
  Lock,
  Radio,
  Server,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/ui/status-badge";
import { Progress } from "@/components/ui/progress";

export default function HomePage() {
  return (
    <div className="max-w-5xl mx-auto space-y-16 py-6 sm:py-10">
      {/* Hero Section */}
      <div className="text-center space-y-6 max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border border-blue-500/20 bg-blue-500/5 text-blue-600 dark:text-blue-400">
          <Sparkles className="h-3.5 w-3.5" />
          <span>Real-Time Service Request Management System</span>
        </div>

        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-foreground leading-[1.15]">
          Asynchronous Service Flow with{" "}
          <span className="text-blue-600 dark:text-blue-500">Zero Request Blocking</span>
        </h1>

        <p className="text-base sm:text-lg text-muted-foreground opacity-80 leading-relaxed max-w-2xl mx-auto">
          ServiceFlow decouples high-volume service request ingestion from background compute, streaming live worker milestones to operators and supervisors over native WebSockets.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <Link href="/dashboard">
            <Button size="lg" className="gap-2 shadow-md">
              <span>Open Operations Console</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>

          <Link href="/login">
            <Button variant="outline" size="lg">
              Sign in with Demo Account
            </Button>
          </Link>
        </div>
      </div>

      {/* Realistic Product Showcase Preview Card */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="h-3 w-3 rounded-full bg-rose-500/80"></div>
            <div className="h-3 w-3 rounded-full bg-amber-500/80"></div>
            <div className="h-3 w-3 rounded-full bg-emerald-500/80"></div>
            <span className="text-xs font-mono text-muted-foreground opacity-70 ml-2">
              serviceflow.internal/operations/live-queue
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              WebSocket Connected (Channel: service_flow:events)
            </span>
          </div>
        </div>

        {/* Live Workload Mock Simulation Display */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="p-5 rounded-xl border border-border bg-slate-50/50 dark:bg-slate-900/40 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
                    In-Flight Worker Job #7C9E6679
                  </span>
                  <h3 className="font-bold text-base mt-0.5">Database Optimization & VACUUM Pipeline</h3>
                </div>
                <StatusBadge status="PROCESSING" />
              </div>

              <div className="space-y-1.5 pt-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-muted-foreground font-medium">Execution Progress</span>
                  <span className="font-bold text-blue-600 font-mono">60%</span>
                </div>
                <Progress value={60} statusVariant="default" />
                <p className="text-[11px] text-muted-foreground opacity-75">
                  Step 3: Executing multi-stage service workload
                </p>
              </div>
            </div>

            {/* Micro Benchmark Telemetry */}
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-3 rounded-lg border border-border bg-background space-y-0.5">
                <div className="text-[10px] uppercase font-semibold text-muted-foreground tracking-wider">
                  Ingestion Latency
                </div>
                <div className="text-base font-bold text-emerald-600 font-mono">&lt; 50ms</div>
              </div>
              <div className="p-3 rounded-lg border border-border bg-background space-y-0.5">
                <div className="text-[10px] uppercase font-semibold text-muted-foreground tracking-wider">
                  Concurrency Multiplier
                </div>
                <div className="text-base font-bold text-blue-600 font-mono">4x Parallel</div>
              </div>
              <div className="p-3 rounded-lg border border-border bg-background space-y-0.5">
                <div className="text-[10px] uppercase font-semibold text-muted-foreground tracking-wider">
                  Event Latency
                </div>
                <div className="text-base font-bold text-purple-600 font-mono">&lt; 150ms</div>
              </div>
            </div>
          </div>

          {/* Real-time Architecture Stack Pill list */}
          <div className="space-y-3 p-4 rounded-xl border border-border bg-background">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Architecture Decoupling
            </h4>
            <div className="space-y-2 text-xs">
              <div className="p-2.5 rounded-lg border border-border flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-blue-600" />
                  <span className="font-medium">FastAPI REST Gateway</span>
                </div>
                <span className="text-[10px] font-mono text-muted-foreground">Non-blocking</span>
              </div>
              <div className="p-2.5 rounded-lg border border-border flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-amber-500" />
                  <span className="font-medium">Celery Worker Pool</span>
                </div>
                <span className="text-[10px] font-mono text-muted-foreground">Redis Broker</span>
              </div>
              <div className="p-2.5 rounded-lg border border-border flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Radio className="h-4 w-4 text-purple-600" />
                  <span className="font-medium">Redis Pub/Sub</span>
                </div>
                <span className="text-[10px] font-mono text-muted-foreground">Sub-second push</span>
              </div>
              <div className="p-2.5 rounded-lg border border-border flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Server className="h-4 w-4 text-emerald-600" />
                  <span className="font-medium">PostgreSQL 16</span>
                </div>
                <span className="text-[10px] font-mono text-muted-foreground">ACID Source of Truth</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Core Architectural Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl border border-border bg-card shadow-sm space-y-3">
          <div className="h-10 w-10 rounded-xl bg-blue-500/10 text-blue-600 flex items-center justify-center">
            <Zap className="h-5 w-5" />
          </div>
          <h3 className="font-semibold text-lg">Asynchronous Ingestion</h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Requests are validated, persisted as <code>QUEUED</code>, and dispatched to Celery workers in sub-millisecond time without stalling HTTP threads.
          </p>
        </div>

        <div className="p-6 rounded-2xl border border-border bg-card shadow-sm space-y-3">
          <div className="h-10 w-10 rounded-xl bg-purple-500/10 text-purple-600 flex items-center justify-center">
            <Radio className="h-5 w-5" />
          </div>
          <h3 className="font-semibold text-lg">Push-Based Streaming</h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Native WebSockets backed by Redis Pub/Sub deliver live progress steps instantly. Eliminates polling overhead and database read storms.
          </p>
        </div>

        <div className="p-6 rounded-2xl border border-border bg-card shadow-sm space-y-3">
          <div className="h-10 w-10 rounded-xl bg-emerald-500/10 text-emerald-600 flex items-center justify-center">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <h3 className="font-semibold text-lg">Deterministic State Machine</h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Strict relational invariants in PostgreSQL: atomic cancellation checks, worker idempotency, and server-side role-based access control.
          </p>
        </div>
      </div>
    </div>
  );
}
