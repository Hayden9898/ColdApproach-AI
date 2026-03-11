"use client";

import { useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { batchSubmit, batchStatus, ApiError } from "@/lib/api";
import { useAppStore } from "@/store/app-store";

interface SubmitArgs {
  urls: string[];
  sendAt?: string;
}

export function useBatchPolling(jobId: string | null) {
  const queryClient = useQueryClient();
  const fromEmail = useAppStore((s) => s.fromEmail);
  const resumeId = useAppStore((s) => s.resumeId);
  const template = useAppStore((s) => s.template);
  const subjectTemplate = useAppStore((s) => s.subjectTemplate);
  const linkedinUrl = useAppStore((s) => s.linkedinUrl);
  const githubUrl = useAppStore((s) => s.githubUrl);
  const setBatchJobId = useAppStore((s) => s.setBatchJobId);

  const submitBatch = useMutation({
    mutationFn: ({ urls, sendAt }: SubmitArgs) =>
      batchSubmit({
        urls,
        from_email: fromEmail,
        resume_id: resumeId,
        mode: "template",
        template,
        subject_template: subjectTemplate,
        linkedin_url: linkedinUrl || null,
        github_url: githubUrl || null,
        send_at: sendAt ?? null,
      }),
    onSuccess: (data) => {
      setBatchJobId(data.job_id);
    },
  });

  const batchData = useQuery({
    queryKey: ["batch-status", jobId],
    queryFn: async () => {
      try {
        return await batchStatus(jobId!);
      } catch (err) {
        // If the job no longer exists (server restarted), clear the stale ID
        if (err instanceof ApiError && err.status === 404) {
          setBatchJobId(null);
          queryClient.removeQueries({ queryKey: ["batch-status"] });
        }
        throw err;
      }
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed") return false;
      return 3000;
    },
    retry: (failureCount, error) => {
      // Don't retry 404s — the job is gone
      if (error instanceof ApiError && error.status === 404) return false;
      return failureCount < 3;
    },
  });

  const reset = useCallback(() => {
    setBatchJobId(null);
    queryClient.removeQueries({ queryKey: ["batch-status"] });
  }, [setBatchJobId, queryClient]);

  const submitError = submitBatch.error
    ? submitBatch.error instanceof ApiError
      ? (submitBatch.error.data as { detail?: string })?.detail ?? "Batch submission failed"
      : submitBatch.error.message
    : null;

  return {
    submitBatch,
    batchData,
    isSubmitting: submitBatch.isPending,
    isPolling: !!jobId && batchData.isFetching && batchData.data?.status !== "completed",
    reset,
    submitError,
  };
}
