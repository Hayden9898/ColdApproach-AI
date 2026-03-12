"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { checkLastAuthenticated, checkGmailStatus, getGmailLoginUrl } from "@/lib/api";
import { useAppStore } from "@/store/app-store";

type AuthStatus = "idle" | "checking" | "connected" | "mismatch" | "error";

const GMAIL_DOMAINS = ["gmail.com", "googlemail.com"];

function isGmailAddress(email: string): boolean {
  const domain = email.trim().toLowerCase().split("@")[1];
  return GMAIL_DOMAINS.includes(domain);
}

export function useEmailAuth(email: string) {
  const [status, setStatus] = useState<AuthStatus>("idle");
  const [mismatchEmail, setMismatchEmail] = useState<string | null>(null);
  const verifiedEmailRef = useRef<string | null>(null);
  const hasCheckedOnMount = useRef(false);
  const setEmailConnected = useAppStore((s) => s.setEmailConnected);
  const emailConnected = useAppStore((s) => s.emailConnected);

  const isGmail = isGmailAddress(email);

  // Reset auth state when email changes
  useEffect(() => {
    if (verifiedEmailRef.current && email.toLowerCase() !== verifiedEmailRef.current) {
      setStatus("idle");
      setMismatchEmail(null);
      setEmailConnected(false);
      verifiedEmailRef.current = null;
    }
  }, [email, setEmailConnected]);

  // On mount: if already connected, restore. Otherwise, check if user just returned from OAuth.
  useEffect(() => {
    if (hasCheckedOnMount.current) return;
    hasCheckedOnMount.current = true;

    if (emailConnected) {
      // Verify the backend still has the OAuth token (lost on server restart)
      checkGmailStatus(email)
        .then((res) => {
          if (res.authenticated) {
            setStatus("connected");
            verifiedEmailRef.current = email.toLowerCase();
          } else {
            setEmailConnected(false);
            setStatus("idle");
          }
        })
        .catch(() => {
          // Backend unreachable — reset to safe state
          setEmailConnected(false);
          setStatus("idle");
        });
    } else if (isGmail) {
      // User may have just returned from OAuth redirect — check once
      setStatus("checking");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // One-time check of last-authenticated (no polling)
  const { data, refetch } = useQuery({
    queryKey: ["gmail-last-authenticated"],
    queryFn: checkLastAuthenticated,
    enabled: status === "checking" && isGmail,
    retry: false,
    staleTime: 0,
  });

  // React to the one-time check result
  useEffect(() => {
    if (status !== "checking") return;

    if (data === undefined) return; // still loading

    if (!data?.email) {
      // No one has authenticated yet — go back to idle
      setStatus("idle");
      return;
    }

    const authedEmail = data.email.toLowerCase();
    const expectedEmail = email.trim().toLowerCase();

    if (authedEmail === expectedEmail) {
      setStatus("connected");
      setEmailConnected(true);
      verifiedEmailRef.current = expectedEmail;
    } else {
      setStatus("mismatch");
      setMismatchEmail(data.email);
    }
  }, [data, status, email, setEmailConnected]);

  // Open Gmail OAuth in a popup/tab (preserves current page state)
  const startAuth = useCallback(() => {
    if (!isGmail) return;

    const popup = window.open(getGmailLoginUrl(), "gmail-auth", "width=500,height=700");

    if (!popup) {
      // Fallback: full-page redirect if popup blocked
      window.location.href = getGmailLoginUrl();
      return;
    }

    const handleMessage = (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return;
      if (event.data?.type === "GMAIL_AUTH_SUCCESS") {
        setStatus("checking");
        refetch();
        window.removeEventListener("message", handleMessage);
      }
    };

    window.addEventListener("message", handleMessage);
  }, [isGmail, refetch]);

  // Reset to idle so user can try again
  const retry = useCallback(() => {
    setStatus("idle");
    setMismatchEmail(null);
    setEmailConnected(false);
    verifiedEmailRef.current = null;
  }, [setEmailConnected]);

  return {
    isGmail,
    status,
    mismatchEmail,
    startAuth,
    retry,
  };
}
