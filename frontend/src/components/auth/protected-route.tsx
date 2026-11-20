"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2, ShieldAlert } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { UserRole } from "@/types";

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { user, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center space-y-3">
        <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
        <p className="text-xs text-muted-foreground font-medium">Validating security session...</p>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div className="max-w-md mx-auto my-12 p-6 rounded-2xl border border-rose-500/20 bg-rose-500/5 text-center space-y-4">
        <div className="h-12 w-12 mx-auto rounded-full bg-rose-500/10 text-rose-600 flex items-center justify-center">
          <ShieldAlert className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h3 className="font-semibold text-lg">Access Restricted</h3>
          <p className="text-xs text-muted-foreground opacity-75">
            Your current role ({user.role}) does not have permission to access this section.
          </p>
        </div>
        <Button onClick={() => router.push("/dashboard")} variant="outline" size="sm">
          Return to Dashboard
        </Button>
      </div>
    );
  }

  return <>{children}</>;
}
