"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ResumeProfile, QueueItem, GenerateEmailResponse } from "@/types/api";
import { DEFAULT_TEMPLATE, DEFAULT_SUBJECT_TEMPLATE } from "@/lib/constants";

interface AppState {
  // Onboarding
  resumeId: string | null;
  resumeProfile: ResumeProfile | null;
  resumePdfDataUrl: string | null;
  linkedinUrl: string;
  githubUrl: string;
  template: string;
  subjectTemplate: string;
  smoothGrammar: boolean;
  fromEmail: string;
  onboardingComplete: boolean;

  // Template drafts (transient, not persisted)
  draftTemplate: string;
  draftSubjectTemplate: string;

  // Dashboard
  queue: QueueItem[];

  // Actions
  setResumeData: (id: string, profile: ResumeProfile) => void;
  setResumePdf: (dataUrl: string | null) => void;
  setLinks: (linkedin: string, github: string) => void;
  setTemplate: (template: string) => void;
  setSubjectTemplate: (subjectTemplate: string) => void;
  setSmoothGrammar: (v: boolean) => void;
  setFromEmail: (email: string) => void;
  setDraftTemplate: (template: string) => void;
  setDraftSubjectTemplate: (subjectTemplate: string) => void;
  completeOnboarding: () => void;
  resetOnboarding: () => void;
  addToQueue: (id: string, url: string) => void;
  updateQueueStatus: (
    id: string,
    status: QueueItem["status"],
    result?: GenerateEmailResponse,
    error?: string,
  ) => void;
  removeFromQueue: (id: string) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      resumeId: null,
      resumeProfile: null,
      resumePdfDataUrl: null,
      linkedinUrl: "",
      githubUrl: "",
      template: DEFAULT_TEMPLATE,
      subjectTemplate: DEFAULT_SUBJECT_TEMPLATE,
      smoothGrammar: true,
      fromEmail: "",
      draftTemplate: DEFAULT_TEMPLATE,
      draftSubjectTemplate: DEFAULT_SUBJECT_TEMPLATE,
      onboardingComplete: false,
      queue: [],

      setResumeData: (id, profile) =>
        set({
          resumeId: id,
          resumeProfile: profile,
          linkedinUrl: profile.linkedin || "",
          githubUrl: profile.github || "",
          fromEmail: profile.email || "",
        }),

      setResumePdf: (dataUrl) => set({ resumePdfDataUrl: dataUrl }),

      setLinks: (linkedin, github) =>
        set({ linkedinUrl: linkedin, githubUrl: github }),

      setTemplate: (template) => set({ template }),
      setSubjectTemplate: (subjectTemplate) => set({ subjectTemplate }),
      setSmoothGrammar: (v) => set({ smoothGrammar: v }),
      setFromEmail: (email) => set({ fromEmail: email }),
      setDraftTemplate: (template) => set({ draftTemplate: template }),
      setDraftSubjectTemplate: (subjectTemplate) => set({ draftSubjectTemplate: subjectTemplate }),

      completeOnboarding: () => set({ onboardingComplete: true }),

      resetOnboarding: () =>
        set({
          resumeId: null,
          resumeProfile: null,
          resumePdfDataUrl: null,
          linkedinUrl: "",
          githubUrl: "",
          template: DEFAULT_TEMPLATE,
          subjectTemplate: DEFAULT_SUBJECT_TEMPLATE,
          fromEmail: "",
          onboardingComplete: false,
          queue: [],
        }),

      addToQueue: (id, url) =>
        set((state) => ({
          queue: [
            { id, url, status: "queued" as const, submittedAt: Date.now() },
            ...state.queue,
          ],
        })),

      updateQueueStatus: (id, status, result, error) =>
        set((state) => ({
          queue: state.queue.map((item) =>
            item.id === id ? { ...item, status, result, error } : item,
          ),
        })),

      removeFromQueue: (id) =>
        set((state) => ({
          queue: state.queue.filter((item) => item.id !== id),
        })),
    }),
    {
      name: "coldapproach-store",
      partialize: (state) => ({
        resumeId: state.resumeId,
        resumeProfile: state.resumeProfile,
        resumePdfDataUrl: state.resumePdfDataUrl,
        linkedinUrl: state.linkedinUrl,
        githubUrl: state.githubUrl,
        template: state.template,
        subjectTemplate: state.subjectTemplate,
        smoothGrammar: state.smoothGrammar,
        fromEmail: state.fromEmail,
        onboardingComplete: state.onboardingComplete,
      }),
    },
  ),
);
