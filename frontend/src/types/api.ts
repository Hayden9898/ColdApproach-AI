// ── Request Types ──────────────────────────────────────

export interface GenerateEmailRequest {
  url: string;
  resume_id?: string | null;
  resume_profile?: Record<string, unknown> | null;
  mode?: "template" | "ml";
  template?: string | null;
  subject_template?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  smooth_grammar?: boolean;
}

export interface SendEmailRequest {
  from_email: string;
  to_email: string;
  subject: string;
  body: string;
  reply_to?: string | null;
  html_body?: string | null;
  send_at?: string | null;
}

export interface BatchSubmitRequest {
  urls: string[];
  from_email: string;
  resume_id?: string | null;
  resume_profile?: Record<string, unknown> | null;
  mode?: "template";
  template?: string | null;
  subject_template?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  smooth_grammar?: boolean;
  send_at?: string | null;
}

// ── Response Types ─────────────────────────────────────

export interface GenerateEmailResponse {
  email: {
    subject: string;
    body: string;
    html_body: string;
    to_email: string | null;
    to_name: string | null;
  };
  contact: {
    name: string;
    title: string | null;
    email: string;
    seniority: string | null;
    confidence: number | null;
  } | null;
  company: {
    name: string | null;
    domain: string | null;
    industry: string | null;
    description: string | null;
    employee_count: number | string | null;
  } | null;
}

export interface SendEmailResponse {
  success: boolean;
  provider: "gmail" | "ses";
  message_id: string | null;
  scheduled: boolean;
  scheduled_at: string | null;
  email_id: string | null;
}

export interface ResumeUploadResponse {
  success: boolean;
  resume_id: string;
  raw_text: string;
  profile: ResumeProfile;
}

export interface ResumeProfile {
  name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  linkedin: string | null;
  github: string | null;
  skills: string[];
  experience: ExperienceEntry[];
  projects: ProjectEntry[];
  education: EducationEntry[];
  summary?: string | null;
  resume_text_length?: number;
}

export interface ExperienceEntry {
  title?: string;
  company?: string;
  duration?: string;
  location?: string;
  description: string | string[];
}

export interface EducationEntry {
  school?: string;
  degree?: string;
  duration?: string;
  gpa?: string;
  location?: string;
  field?: string;
}

export interface ProjectEntry {
  name?: string;
  technologies?: string;
  duration?: string;
  description: string | string[];
}

export interface BatchStatusResponse {
  job_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  total: number;
  completed: number;
  failed: number;
  results: Record<string, unknown>;
}

// ── Frontend-only State Types ──────────────────────────

export type ProcessingStatus = "queued" | "processing" | "completed" | "failed";

export interface QueueItem {
  id: string;
  url: string;
  status: ProcessingStatus;
  submittedAt: number;
  result?: GenerateEmailResponse;
  error?: string;
}
