import { Activity, Layers, Radio, ShieldCheck, Zap } from "lucide-react";

export default function HomePage() {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="space-y-3">
        <h2 className="text-3xl font-bold tracking-tight">System Operational Overview</h2>
        <p className="text-base opacity-75">
          ServiceFlow decouples high-throughput request ingestion from background execution, streaming live progress updates via native WebSockets.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-xl border border-border bg-card shadow-sm space-y-3">
          <div className="h-10 w-10 rounded-lg bg-blue-500/10 text-blue-600 flex items-center justify-center">
            <Zap className="h-5 w-5" />
          </div>
          <h3 className="font-semibold text-lg">Non-blocking Ingestion</h3>
          <p className="text-sm opacity-75">
            FastAPI REST gateway accepts service requests in sub-millisecond time and hands off to Celery workers.
          </p>
        </div>

        <div className="p-6 rounded-xl border border-border bg-card shadow-sm space-y-3">
          <div className="h-10 w-10 rounded-lg bg-purple-500/10 text-purple-600 flex items-center justify-center">
            <Radio className="h-5 w-5" />
          </div>
          <h3 className="font-semibold text-lg">WebSocket Streaming</h3>
          <p className="text-sm opacity-75">
            Direct real-time event distribution over Redis Pub/Sub eliminating database polling overhead.
          </p>
        </div>

        <div className="p-6 rounded-xl border border-border bg-card shadow-sm space-y-3">
          <div className="h-10 w-10 rounded-lg bg-emerald-500/10 text-emerald-600 flex items-center justify-center">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <h3 className="font-semibold text-lg">Deterministic State</h3>
          <p className="text-sm opacity-75">
            Transactional state machine in PostgreSQL with atomic cancellation guards and worker idempotency.
          </p>
        </div>
      </div>

      <div className="p-6 rounded-xl border border-border bg-card shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-emerald-500" />
          <h3 className="font-semibold text-lg">Phase 4 Scaffold Verification</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div className="p-4 rounded-lg bg-background border border-border space-y-1">
            <div className="text-xs uppercase tracking-wider font-semibold opacity-60">Frontend Architecture</div>
            <div className="font-medium">Next.js App Router (TypeScript + Tailwind CSS)</div>
            <div className="text-xs text-emerald-600 font-medium">Initialized & Build Verified</div>
          </div>
          <div className="p-4 rounded-lg bg-background border border-border space-y-1">
            <div className="text-xs uppercase tracking-wider font-semibold opacity-60">Backend Architecture</div>
            <div className="font-medium">FastAPI (Python 3.12 + Async SQLAlchemy)</div>
            <div className="text-xs text-emerald-600 font-medium">Scaffolded with Health Probes</div>
          </div>
        </div>
      </div>
    </div>
  );
}
