import type {
  GenerateEmailRequest,
  GenerateEmailResponse,
  SendEmailRequest,
  SendEmailResponse,
  ResumeUploadResponse,
  BatchSubmitRequest,
  BatchStatusResponse,
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

class ApiError extends Error {
  constructor(
    public status: number,
    public data: unknown,
  ) {
    super(`API error ${status}`);
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers);
  if (API_KEY) {
    headers.set("Authorization", `Bearer ${API_KEY}`);
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new ApiError(res.status, data);
  }
  return res.json();
}

export async function uploadResume(file: File): Promise<ResumeUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return request<ResumeUploadResponse>("/resume/upload", {
    method: "POST",
    body: formData,
  });
}

export async function generateEmail(
  req: GenerateEmailRequest,
): Promise<GenerateEmailResponse> {
  return request<GenerateEmailResponse>("/scrape/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export async function sendEmail(
  req: SendEmailRequest,
): Promise<SendEmailResponse> {
  return request<SendEmailResponse>("/send/email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export async function checkGmailStatus(
  email: string,
): Promise<{ authenticated: boolean; email: string }> {
  return request(`/auth/gmail/status?email=${encodeURIComponent(email)}`);
}

export async function batchSubmit(
  req: BatchSubmitRequest,
): Promise<{ success: boolean; job_id: string; status: string; total: number }> {
  return request("/batch/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export async function batchStatus(
  jobId: string,
): Promise<BatchStatusResponse> {
  return request(`/batch/${jobId}/status`);
}

export async function checkLastAuthenticated(): Promise<{ email: string | null }> {
  return request("/auth/gmail/last-authenticated");
}

export function getGmailLoginUrl(): string {
  return `${API_BASE}/auth/gmail/login`;
}

export { ApiError };
