"use client";

import Link from "next/link";
import { ArrowRight, FileText, Layers, PlusCircle, Shield, User } from "lucide-react";
import { ProtectedRoute } from "@/components/auth/protected-route";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/use-auth";

export default function DashboardPage() {
  const { user } = useAuth();

  if (!user) return null;

  const isOperator = user.role === "OPERATOR";
  const isSupervisorOrAdmin = user.role === "SUPERVISOR" || user.role === "ADMIN";

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
              ServiceFlow Operations Console &bull; Authenticated Session Active
            </p>
          </div>

          <Link href="/requests/new">
            <Button className="gap-2">
              <PlusCircle className="h-4 w-4" />
              Create Service Request
            </Button>
          </Link>
        </div>

        {/* Operational Modules Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="hover:border-blue-500/50 transition-colors">
            <CardHeader className="space-y-1">
              <div className="h-10 w-10 rounded-xl bg-blue-500/10 text-blue-600 flex items-center justify-center mb-2">
                <FileText className="h-5 w-5" />
              </div>
              <CardTitle className="text-lg">
                {isOperator ? "My Service Requests" : "Global Request Queue"}
              </CardTitle>
              <CardDescription>
                {isOperator
                  ? "Inspect, search, and track your submitted service requests in real time."
                  : "Monitor and audit all service requests across the organization."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/requests">
                <Button variant="outline" className="w-full justify-between">
                  <span>View All Requests</span>
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="hover:border-emerald-500/50 transition-colors">
            <CardHeader className="space-y-1">
              <div className="h-10 w-10 rounded-xl bg-emerald-500/10 text-emerald-600 flex items-center justify-center mb-2">
                <PlusCircle className="h-5 w-5" />
              </div>
              <CardTitle className="text-lg">New Request Submission</CardTitle>
              <CardDescription>
                Submit asynchronous workloads to the background processing queue with non-blocking ingestion.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/requests/new">
                <Button variant="outline" className="w-full justify-between">
                  <span>Open Submission Form</span>
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* Role Permissions Information Card */}
        <Card className="border-border">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-blue-600" />
              <CardTitle className="text-base">Role Governance & Scope</CardTitle>
            </div>
            <CardDescription>
              Your system capabilities are strictly determined by your assigned account role.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-xs space-y-2 text-muted-foreground">
            {isOperator && (
              <p>
                <strong>Operator Mode:</strong> You can submit new requests, view and search your own requests, and cancel your own requests while they remain in <code>QUEUED</code> state.
              </p>
            )}
            {isSupervisorOrAdmin && (
              <p>
                <strong>Supervisor / Admin Mode:</strong> You have global oversight across all operators, can inspect live progress across the background worker pool, and can cancel any queued request.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}
