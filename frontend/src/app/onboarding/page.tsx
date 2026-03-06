"use client";

import { Logo } from "@/components/shared/logo";

export default function OnboardingPage() {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <Logo className="text-lg" />
        <p className="text-sm text-muted-foreground">
          Onboarding — Step 2 will build this out.
        </p>
      </div>
    </div>
  );
}
