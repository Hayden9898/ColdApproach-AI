"use client";

import { useMutation } from "@tanstack/react-query";
import { uploadResume, ApiError } from "@/lib/api";
import { useAppStore } from "@/store/app-store";

export function useResumeUpload() {
  const setResumeData = useAppStore((s) => s.setResumeData);

  return useMutation({
    mutationFn: uploadResume,
    onSuccess: (data) => {
      setResumeData(data.resume_id, data.profile);
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        const detail =
          (error.data as { detail?: string })?.detail ?? "Upload failed";
        throw new Error(detail);
      }
    },
  });
}
