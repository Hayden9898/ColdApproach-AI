"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { checkGmailStatus, getGmailLoginUrl } from "@/lib/api";
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
  const setJwt = useAppStore((s) => s.setJwt);
  const setFromEmail = useAppStore((s) => s.setFromEmail);
  const emailConnected = useAppStore((s) => s.emailConnected);
  const jwt = useAppStore((s) => s.jwt);

  const isGmail = isGmailAddress(email);

  // Reset auth state when email changes
  useEffect(() => {
    if (verifiedEmailRef.current && email.toLowerCase() !== verifiedEmailRef.current) {
      setStatus("idle");
      setMismatchEmail(null);
      setEmailConnected(false);
      setJwt(null);
      verifiedEmailRef.current = null;
    }
  }, [email, setEmailConnected, setJwt]);

  // On mount: if already connected with a JWT, verify the backend still has the OAuth token
  useEffect(() => {
    if (hasCheckedOnMount.current) return;
    hasCheckedOnMount.current = true;

    if (emailConnected && jwt) {
      checkGmailStatus(email)
        .then((res) => {
          if (res.authenticated) {
            setStatus("connected");
            verifiedEmailRef.current = email.toLowerCase();
          } else {
            setEmailConnected(false);
            setJwt(null);
            setStatus("idle");
          }
        })
        .catch(() => {
          setEmailConnected(false);
          setJwt(null);
          setStatus("idle");
        });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Open Gmail OAuth in a popup/tab (preserves current page state)
  const startAuth = useCallback(() => {
    if (!isGmail) return;

    const popup = window.open(getGmailLoginUrl(), "gmail-auth", "width=500,height=700");

    if (!popup) {
      window.location.href = getGmailLoginUrl();
      return;
    }

    let resolved = false;

    const handleAuthSuccess = (authJwt: string, authEmail: string) => {
      if (resolved) return;
      resolved = true;
      window.removeEventListener("message", handleMessage);

      const expectedEmail = email.trim().toLowerCase();
      if (authEmail.toLowerCase() === expectedEmail) {
        setJwt(authJwt);
        setFromEmail(authEmail);
        setEmailConnected(true);
        setStatus("connected");
        verifiedEmailRef.current = expectedEmail;
      } else {
        setStatus("mismatch");
        setMismatchEmail(authEmail);
      }
    };

    // Primary: postMessage from the callback page
    const handleMessage = (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return;
      if (event.data?.type === "GMAIL_AUTH_SUCCESS" && event.data.jwt) {
        handleAuthSuccess(event.data.jwt, event.data.email);
      }
    };

    window.addEventListener("message", handleMessage);

    // Fallback: detect when popup/tab closes without postMessage
    const poll = setInterval(() => {
      if (popup.closed) {
        clearInterval(poll);
        if (!resolved) {
          resolved = true;
          window.removeEventListener("message", handleMessage);
          // Popup closed without sending message — user may have cancelled
          setStatus("idle");
        }
      }
    }, 500);
  }, [isGmail, email, setJwt, setFromEmail, setEmailConnected]);

  // Reset to idle so user can try again
  const retry = useCallback(() => {
    setStatus("idle");
    setMismatchEmail(null);
    setEmailConnected(false);
    setJwt(null);
    verifiedEmailRef.current = null;
  }, [setEmailConnected, setJwt]);

  return {
    isGmail,
    status,
    mismatchEmail,
    startAuth,
    retry,
  };
}
