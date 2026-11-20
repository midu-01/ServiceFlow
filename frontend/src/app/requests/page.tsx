"use client";

import { useAuth } from "@/hooks/use-auth";
import { ProtectedRoute } from "@/components/auth/protected-route";
import { RequestList } from "@/features/requests/request-list";

export default function RequestsPage() {
  const { user } = useAuth();
  const isOperator = user?.role === "OPERATOR";

  return (
    <ProtectedRoute>
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {isOperator ? "My Service Requests" : "Global Service Request Queue"}
          </h1>
          <p className="text-xs text-muted-foreground opacity-75 mt-1">
            {isOperator
              ? "Monitor the lifecycle and live processing progress of your submitted service requests."
              : "Supervisor oversight of all incoming and in-flight background worker service requests."}
          </p>
        </div>

        <RequestList />
      </div>
    </ProtectedRoute>
  );
}
