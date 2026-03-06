"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAppStore } from "@/store/app-store";
import { Logo } from "@/components/shared/logo";

export default function Home() {
  const router = useRouter();
  const onboardingComplete = useAppStore((s) => s.onboardingComplete);

  useEffect(() => {
    router.replace(onboardingComplete ? "/dashboard" : "/onboarding");
  }, [onboardingComplete, router]);

  return (
    <div className="flex h-screen items-center justify-center">
      <Logo className="text-lg" />
    </div>
  );
}
