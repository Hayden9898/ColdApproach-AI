"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Logo } from "@/components/shared/logo";
import { StepIndicator } from "@/components/onboarding/step-indicator";
import { ResumeUpload } from "@/components/onboarding/resume-upload";
import { ProfileSetup } from "@/components/onboarding/profile-setup";
import { TemplateEditor } from "@/components/onboarding/template-editor";
import { EmailPreview } from "@/components/onboarding/email-preview";
import { UrlSubmit } from "@/components/onboarding/url-submit";
import { Button } from "@/components/ui/button";
import { slideRight, fadeIn, DURATION } from "@/lib/animations";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/store/app-store";
import dynamic from "next/dynamic";

const PdfViewer = dynamic(
  () =>
    import("@/components/onboarding/pdf-viewer").then((mod) => mod.PdfViewer),
  { ssr: false },
);
import { ArrowRight, Globe, UserSearch, Mail, Send } from "lucide-react";

const STEPS = ["Resume", "Profile", "Template", "Send"];

const HOW_IT_WORKS = [
  {
    icon: Globe,
    title: "Paste a company URL",
    desc: "We scrape their website to understand what they do.",
  },
  {
    icon: UserSearch,
    title: "We find the right contact",
    desc: "Hunter.io discovers and ranks contacts by role fit.",
  },
  {
    icon: Mail,
    title: "AI writes your email",
    desc: "Your template is personalized with company + contact context.",
  },
  {
    icon: Send,
    title: "Send or schedule",
    desc: "Send immediately via Gmail or SES, or schedule for later.",
  },
];

export default function OnboardingPage() {
  const pdfDataUrl = useAppStore((s) => s.resumePdfDataUrl);
  const storedStep = useAppStore((s) => s.onboardingStep);
  const storedStarted = useAppStore((s) => s.onboardingStarted);
  const setOnboardingStep = useAppStore((s) => s.setOnboardingStep);
  const setOnboardingStarted = useAppStore((s) => s.setOnboardingStarted);

  // Wait for Zustand to hydrate from localStorage before rendering
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => {
    if (useAppStore.persist.hasHydrated()) {
      setHydrated(true);
    } else {
      return useAppStore.persist.onFinishHydration(() => setHydrated(true));
    }
  }, []);

  // Local state for React rendering, initialized after hydration
  const [started, setStartedLocal] = useState(false);
  const [step, setStepLocal] = useState(0);

  // Restore from persisted store after hydration (runs once)
  const hasRestoredRef = useRef(false);
  useEffect(() => {
    if (!hydrated || hasRestoredRef.current) return;
    hasRestoredRef.current = true;
    setStartedLocal(storedStarted);
    setStepLocal(storedStep);
  }, [hydrated, storedStarted, storedStep]);

  // Navigation helpers — sync local state + persisted store
  const setStep = (s: number) => {
    setStepLocal(s);
    setOnboardingStep(s);
  };
  const setStarted = (s: boolean) => {
    setStartedLocal(s);
    setOnboardingStarted(s);
  };

  // Don't render until store is hydrated — prevents flash of wrong step
  if (!hydrated) return null;

  // Intro screen — before the numbered steps
  if (!started) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center px-6">
        <AnimatePresence>
          <motion.div
            className="w-full max-w-md space-y-8"
            variants={fadeIn}
            initial="initial"
            animate="animate"
            transition={{ duration: DURATION.slow }}
          >
            <div className="space-y-3">
              <Logo className="text-lg" />
              <h1 className="text-lg font-semibold tracking-tight">
                Personalized cold outreach, automated.
              </h1>
              <p className="text-sm text-muted-foreground leading-relaxed">
                ColdApproach takes a company URL and your resume, finds the
                right person to contact, and generates a personalized email
                using your template — in seconds.
              </p>
            </div>

            <div className="space-y-1">
              <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                How it works
              </p>
              <div className="space-y-0">
                {HOW_IT_WORKS.map((item, i) => (
                  <div
                    key={item.title}
                    className="flex items-start gap-3 py-3 border-b border-border last:border-0"
                  >
                    <div className="flex h-6 w-6 items-center justify-center rounded-sm bg-secondary shrink-0 mt-0.5">
                      <item.icon className="h-3.5 w-3.5 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">
                        <span className="text-muted-foreground font-mono text-xs mr-1.5">
                          {i + 1}.
                        </span>
                        {item.title}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {item.desc}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <Button onClick={() => setStarted(true)} size="sm" className="gap-1.5">
              Get started
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </motion.div>
        </AnimatePresence>
      </div>
    );
  }

  // Numbered step flow
  const isTemplateStep = step === 2;

  return (
    <div
      className={cn(
        "flex flex-col items-center px-6",
        isTemplateStep ? "h-screen py-6" : "min-h-screen py-12",
      )}
    >
      <div
        className={cn(
          "w-full max-w-5xl",
          isTemplateStep
            ? "flex flex-col flex-1 min-h-0 gap-4"
            : "space-y-8",
        )}
      >
        <div className="flex items-center justify-between shrink-0">
          <Logo />
          <StepIndicator steps={STEPS} current={step} />
        </div>

        <div
          className={cn(
            step === 0 && pdfDataUrl && "grid grid-cols-1 lg:grid-cols-2 gap-8",
            isTemplateStep && "flex-1 min-h-0",
          )}
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              variants={slideRight}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: DURATION.normal }}
              className={isTemplateStep ? "h-full" : undefined}
            >
              {step === 0 && (
                <ResumeUpload
                  onComplete={() => setStep(1)}
                  onBack={() => setStarted(false)}
                />
              )}

              {step === 1 && (
                <ProfileSetup
                  onComplete={() => setStep(2)}
                  onBack={() => setStep(0)}
                />
              )}

              {step === 2 && (
                <div className="flex flex-col h-full gap-4">
                  <div className="shrink-0">
                    <h2 className="text-lg font-semibold tracking-tight">
                      Configure your template
                    </h2>
                    <p className="text-sm text-muted-foreground mt-1">
                      Customize your email template. Placeholders in brackets
                      will be filled automatically when emails are generated.
                    </p>
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-8 flex-1 min-h-0">
                    <TemplateEditor
                      onComplete={() => setStep(3)}
                      onBack={() => setStep(1)}
                    />
                    <div className="hidden lg:block min-h-0">
                      <EmailPreview />
                    </div>
                  </div>
                </div>
              )}

              {step === 3 && (
                <UrlSubmit onBack={() => setStep(2)} />
              )}
            </motion.div>
          </AnimatePresence>

          {step === 0 && pdfDataUrl && (
            <div className="hidden lg:block">
              <PdfViewer src={pdfDataUrl} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
