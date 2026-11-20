"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, PlusCircle, Sparkles } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { apiClient, ApiClientError } from "@/lib/api/client";
import { requestKeys } from "@/lib/api/query-keys";
import { ApiResponse, ServiceRequest } from "@/types";

const requestSchema = z.object({
  title: z
    .string()
    .min(3, "Title must be at least 3 characters")
    .max(100, "Title must not exceed 100 characters"),
  description: z
    .string()
    .min(10, "Description must be at least 10 characters")
    .max(1000, "Description must not exceed 1000 characters"),
});

type RequestFormData = z.infer<typeof requestSchema>;

const PRESET_TEMPLATES = [
  {
    name: "Database Vacuum & Index",
    title: "Database Optimization & Maintenance",
    description: "Run VACUUM ANALYZE and re-index high-throughput operational tables across primary clusters.",
  },
  {
    name: "Customer Order Sync",
    title: "Batch Customer Order Synchronization",
    description: "Extract, transform, and synchronize customer transaction records with downstream data warehouses.",
  },
  {
    name: "Audit Telemetry Export",
    title: "System Audit & Telemetry Archival",
    description: "Compile and compress immutable operational telemetry logs for seasonal compliance review.",
  },
];

export function RequestCreateForm() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<RequestFormData>({
    resolver: zodResolver(requestSchema),
    defaultValues: {
      title: "",
      description: "",
    },
  });

  const titleValue = watch("title") || "";
  const descriptionValue = watch("description") || "";

  const onSubmit = async (data: RequestFormData) => {
    setIsSubmitting(true);
    setServerError(null);

    try {
      const res = await apiClient<ApiResponse<ServiceRequest>>(
        "/api/v1/service-requests",
        {
          method: "POST",
          body: JSON.stringify(data),
        }
      );

      // Invalidate queries so lists update immediately
      await queryClient.invalidateQueries({ queryKey: requestKeys.all });
      router.push(`/requests/${res.data.id}`);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setServerError(err.message);
      } else {
        setServerError("Failed to submit service request. Please check your connection.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const applyTemplate = (template: typeof PRESET_TEMPLATES[0]) => {
    setValue("title", template.title, { shouldValidate: true });
    setValue("description", template.description, { shouldValidate: true });
    setServerError(null);
  };

  return (
    <div className="space-y-6">
      {serverError && (
        <Alert variant="destructive">
          <AlertTitle>Submission Error</AlertTitle>
          <AlertDescription>{serverError}</AlertDescription>
        </Alert>
      )}

      {/* Preset Scenario Quick-Picks */}
      <div className="p-4 rounded-xl border border-border bg-slate-50 dark:bg-slate-900/40 space-y-2.5">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          <Sparkles className="h-3.5 w-3.5 text-amber-500" />
          <span>Quick Scenarios:</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {PRESET_TEMPLATES.map((tmpl) => (
            <Button
              key={tmpl.name}
              type="button"
              variant="outline"
              size="sm"
              onClick={() => applyTemplate(tmpl)}
              className="text-xs bg-card"
            >
              {tmpl.name}
            </Button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Title */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-center text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <label htmlFor="title">Request Title</label>
            <span className={titleValue.length > 100 ? "text-rose-500 font-bold" : "opacity-60"}>
              {titleValue.length}/100
            </span>
          </div>
          <Input
            id="title"
            placeholder="e.g. Production Data Synchronization"
            error={errors.title?.message}
            {...register("title")}
          />
        </div>

        {/* Description */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-center text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <label htmlFor="description">Detailed Description</label>
            <span className={descriptionValue.length > 1000 ? "text-rose-500 font-bold" : "opacity-60"}>
              {descriptionValue.length}/1000
            </span>
          </div>
          <Textarea
            id="description"
            rows={5}
            placeholder="Explain the technical scope and operations to be executed by background workers..."
            error={errors.description?.message}
            {...register("description")}
          />
        </div>

        {/* Submit & Cancel Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-border">
          <Link href="/requests">
            <Button type="button" variant="ghost" className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
          </Link>

          <Button type="submit" isLoading={isSubmitting} className="gap-2">
            <PlusCircle className="h-4 w-4" />
            Submit Request
          </Button>
        </div>
      </form>
    </div>
  );
}
