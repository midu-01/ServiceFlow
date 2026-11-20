import { Metadata } from "next";
import { ProtectedRoute } from "@/components/auth/protected-route";
import { RequestDetail } from "@/features/requests/request-detail";

interface PageProps {
  params: Promise<{ id: string }>;
}

export const metadata: Metadata = {
  title: "Service Request Details | ServiceFlow",
  description: "Live progress tracking and execution details for background service request",
};

export default async function RequestDetailPage({ params }: PageProps) {
  const { id } = await params;

  return (
    <ProtectedRoute>
      <div className="py-6">
        <RequestDetail requestId={id} />
      </div>
    </ProtectedRoute>
  );
}
