import { Metadata } from "next";
import { ProtectedRoute } from "@/components/auth/protected-route";
import { RequestCreateForm } from "@/features/requests/request-create-form";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export const metadata: Metadata = {
  title: "New Service Request | ServiceFlow",
  description: "Submit a new asynchronous background service request",
};

export default function NewRequestPage() {
  return (
    <ProtectedRoute>
      <div className="max-w-2xl mx-auto py-6 space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Create Service Request</h1>
          <p className="text-xs text-muted-foreground opacity-75 mt-1">
            Workloads are dispatched to independent Celery workers and execute concurrently without blocking the API.
          </p>
        </div>

        <Card className="border-border shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">Request Specification</CardTitle>
            <CardDescription>
              Provide clear operational parameters for the background execution pipeline.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <RequestCreateForm />
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}
