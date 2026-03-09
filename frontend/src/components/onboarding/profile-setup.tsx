"use client";

import { useState } from "react";
import { ArrowLeft, AlertCircle, Phone, MapPin, Check, Loader2, Mail } from "lucide-react";
import { useEmailAuth } from "@/hooks/use-email-auth";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/store/app-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface ProfileSetupProps {
  onComplete: () => void;
  onBack: () => void;
}

interface FieldErrors {
  name?: string;
  email?: string;
  linkedin?: string;
  github?: string;
}

type FieldKey = keyof FieldErrors;

const SOFT_FIELDS: FieldKey[] = ["linkedin", "github"];

function normalizeUrl(value: string, domain: string): string {
  const trimmed = value.trim();
  if (!trimmed) return trimmed;
  if (trimmed.includes(domain) && !trimmed.startsWith("http")) {
    return `https://${trimmed}`;
  }
  return trimmed;
}

function validate(values: {
  name: string;
  email: string;
  linkedin: string;
  github: string;
}): { errors: FieldErrors; hasHardErrors: boolean } {
  const errors: FieldErrors = {};

  if (!values.name.trim()) {
    errors.name = "Name is required";
  }

  if (!values.email.trim()) {
    errors.email = "Sender email is required";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email.trim())) {
    errors.email = "Enter a valid email address";
  }

  if (
    values.linkedin.trim() &&
    !/https?:\/\/.*(linkedin\.com\/in\/).+/i.test(values.linkedin.trim())
  ) {
    errors.linkedin = "Should be a LinkedIn profile URL (linkedin.com/in/...)";
  }

  if (
    values.github.trim() &&
    !/https?:\/\/.*(github\.com\/).+/i.test(values.github.trim())
  ) {
    errors.github = "Should be a GitHub profile URL (github.com/...)";
  }

  const hasHardErrors = !!errors.name || !!errors.email;
  return { errors, hasHardErrors };
}

function inputClass(field: FieldKey, touched: Record<string, boolean>, errors: FieldErrors) {
  const isTouched = touched[field];
  const hasError = errors[field];
  const isSoft = SOFT_FIELDS.includes(field);

  if (!isTouched) return "font-mono text-sm";
  if (hasError && isSoft) return "font-mono text-sm border-amber-500/50";
  if (hasError) return "font-mono text-sm border-destructive";
  return "font-mono text-sm border-green-500/50";
}

export function ProfileSetup({ onComplete, onBack }: ProfileSetupProps) {
  const resumeProfile = useAppStore((s) => s.resumeProfile);
  const linkedinUrl = useAppStore((s) => s.linkedinUrl);
  const githubUrl = useAppStore((s) => s.githubUrl);
  const fromEmail = useAppStore((s) => s.fromEmail);
  const setLinks = useAppStore((s) => s.setLinks);
  const setFromEmail = useAppStore((s) => s.setFromEmail);
  const emailConnected = useAppStore((s) => s.emailConnected);

  const [name, setName] = useState(resumeProfile?.name ?? "");
  const [email, setEmail] = useState(fromEmail || resumeProfile?.email || "");
  const [linkedin, setLinkedin] = useState(linkedinUrl || "");
  const [github, setGithub] = useState(githubUrl || "");
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  // Derived validation — recomputed on every render
  const { errors, hasHardErrors } = validate({
    name,
    email,
    linkedin: normalizeUrl(linkedin, "linkedin.com"),
    github: normalizeUrl(github, "github.com"),
  });

  const emailValid = email.trim() !== "" && !errors.email;
  const { isGmail, status: authStatus, mismatchEmail, startAuth, retry } = useEmailAuth(email);

  const handleBlur = (field: string) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
  };

  if (!resumeProfile) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>No resume data found. Please go back and upload your resume.</span>
        </div>
        <Button
          onClick={onBack}
          variant="ghost"
          size="sm"
          className="gap-1.5 hover:bg-transparent hover:text-primary dark:hover:bg-transparent"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back
        </Button>
      </div>
    );
  }

  const handleContinue = () => {
    // Mark all fields as touched to surface any remaining errors
    setTouched({ name: true, email: true, linkedin: true, github: true });
    if (hasHardErrors || !emailConnected) return;

    const normalizedLinkedin = normalizeUrl(linkedin, "linkedin.com");
    const normalizedGithub = normalizeUrl(github, "github.com");

    // Persist to store
    setLinks(normalizedLinkedin, normalizedGithub);
    setFromEmail(email.trim());
    useAppStore.setState((state) => ({
      resumeProfile: state.resumeProfile
        ? { ...state.resumeProfile, name: name.trim() }
        : state.resumeProfile,
    }));

    onComplete();
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">
          Verify your profile
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Confirm your details below. These will be used in your outgoing emails.
        </p>
      </div>

      <div className="border border-border bg-card rounded-lg divide-y divide-border">
        {/* Identity */}
        <div className="p-4 space-y-3">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Identity
          </p>
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground">Full name</label>
            <div className="relative">
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                onBlur={() => handleBlur("name")}
                placeholder="Your name"
                className={cn(inputClass("name", touched, errors), touched.name && !errors.name && "pr-8")}
              />
              {touched.name && !errors.name && (
                <Check className="absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-green-500" />
              )}
            </div>
            {touched.name && errors.name && (
              <p className="text-xs text-destructive">{errors.name}</p>
            )}
          </div>
          {(resumeProfile.phone || resumeProfile.location) && (
            <div className="flex gap-4 text-xs text-muted-foreground font-mono">
              {resumeProfile.phone && (
                <span className="flex items-center gap-1">
                  <Phone className="h-3 w-3" />
                  {resumeProfile.phone}
                </span>
              )}
              {resumeProfile.location && (
                <span className="flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  {resumeProfile.location}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Links */}
        <div className="p-4 space-y-3">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Links
          </p>
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground">LinkedIn</label>
            <div className="relative">
              <Input
                value={linkedin}
                onChange={(e) => setLinkedin(e.target.value)}
                onBlur={() => handleBlur("linkedin")}
                placeholder="https://linkedin.com/in/yourprofile"
                className={cn(inputClass("linkedin", touched, errors), touched.linkedin && !errors.linkedin && linkedin.trim() && "pr-8")}
              />
              {touched.linkedin && !errors.linkedin && linkedin.trim() && (
                <Check className="absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-green-500" />
              )}
            </div>
            {touched.linkedin && errors.linkedin && (
              <p className="text-xs text-amber-500">{errors.linkedin}</p>
            )}
          </div>
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground">GitHub</label>
            <div className="relative">
              <Input
                value={github}
                onChange={(e) => setGithub(e.target.value)}
                onBlur={() => handleBlur("github")}
                placeholder="https://github.com/yourhandle"
                className={cn(inputClass("github", touched, errors), touched.github && !errors.github && github.trim() && "pr-8")}
              />
              {touched.github && !errors.github && github.trim() && (
                <Check className="absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-green-500" />
              )}
            </div>
            {touched.github && errors.github && (
              <p className="text-xs text-amber-500">{errors.github}</p>
            )}
          </div>
        </div>

        {/* Sender email */}
        <div className="p-4 space-y-3">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Sender email
          </p>
          <p className="text-xs text-muted-foreground">
            Cold emails will be sent from this address.
          </p>
          <div className="space-y-1.5">
            <div className="relative">
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onBlur={() => handleBlur("email")}
                placeholder="you@gmail.com"
                className={cn(inputClass("email", touched, errors), touched.email && !errors.email && "pr-8")}
              />
              {touched.email && !errors.email && (
                <Check className="absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-green-500" />
              )}
            </div>
            {touched.email && errors.email && (
              <p className="text-xs text-destructive">{errors.email}</p>
            )}
          </div>

          {/* Inline email auth */}
          {emailValid && (
            <div className="rounded-md border border-border bg-secondary/30 p-3 space-y-2">
              {isGmail ? (
                <>
                  {authStatus === "idle" && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">Gmail account</span>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs gap-1.5"
                        onClick={() => {
                          setFromEmail(email.trim());
                          startAuth();
                        }}
                      >
                        Connect Gmail
                      </Button>
                    </div>
                  )}

                  {authStatus === "checking" && (
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                      <span className="text-xs text-muted-foreground">
                        Verifying connection...
                      </span>
                    </div>
                  )}

                  {authStatus === "connected" && (
                    <div className="flex items-center gap-2">
                      <Check className="h-3.5 w-3.5 text-green-500" />
                      <span className="text-xs text-green-600 dark:text-green-400 font-medium">
                        Gmail connected
                      </span>
                    </div>
                  )}

                  {authStatus === "mismatch" && (
                    <div className="space-y-2">
                      <div className="flex items-start gap-2">
                        <AlertCircle className="h-3.5 w-3.5 text-destructive shrink-0 mt-0.5" />
                        <p className="text-xs text-destructive">
                          You signed in as <span className="font-mono font-medium">{mismatchEmail}</span> but
                          entered <span className="font-mono font-medium">{email}</span>. Please sign in
                          with the correct account.
                        </p>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs"
                        onClick={retry}
                      >
                        Try again
                      </Button>
                    </div>
                  )}

                  {authStatus === "error" && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <AlertCircle className="h-3.5 w-3.5 text-destructive" />
                        <span className="text-xs text-destructive">Authentication failed</span>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs"
                        onClick={retry}
                      >
                        Try again
                      </Button>
                    </div>
                  )}
                </>
              ) : (
                <div className="flex items-center gap-2">
                  <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">
                    Custom domain email support coming soon. Use a Gmail address to send emails.
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-between">
        <Button
          onClick={onBack}
          variant="ghost"
          size="sm"
          className="gap-1.5 hover:bg-transparent hover:text-primary dark:hover:bg-transparent"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back
        </Button>
        <Button onClick={handleContinue} size="sm" disabled={!emailConnected}>
          Continue
        </Button>
      </div>
    </div>
  );
}
