"use client";

import React from "react";
import { AlertTriangle } from "lucide-react";
import {
  Dialog,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface CancelDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  requestTitle: string;
  isCancelling: boolean;
  onConfirm: () => void;
}

export function CancelDialog({
  open,
  onOpenChange,
  requestTitle,
  isCancelling,
  onConfirm,
}: CancelDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogHeader>
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-rose-500/10 text-rose-600 flex items-center justify-center shrink-0">
            <AlertTriangle className="h-5 w-5" />
          </div>
          <div>
            <DialogTitle>Cancel Service Request?</DialogTitle>
            <DialogDescription>
              Are you sure you want to cancel{" "}
              <strong className="text-foreground font-semibold">&ldquo;{requestTitle}&rdquo;</strong>?
            </DialogDescription>
          </div>
        </div>
      </DialogHeader>

      <p className="text-xs text-muted-foreground opacity-80 leading-relaxed">
        This action transitions the request to <code>CANCELLED</code> and removes it from the active worker queue.
        Requests that have already transitioned to processing cannot be cancelled.
      </p>

      <DialogFooter>
        <Button
          variant="outline"
          onClick={() => onOpenChange(false)}
          disabled={isCancelling}
        >
          Keep Request
        </Button>
        <Button
          variant="destructive"
          onClick={onConfirm}
          isLoading={isCancelling}
        >
          Confirm Cancellation
        </Button>
      </DialogFooter>
    </Dialog>
  );
}
