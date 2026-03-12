"use client";

import { useEffect } from "react";
import { useSearchParams } from "next/navigation";

/**
 * OAuth callback landing page — opened inside a popup/tab by startAuth().
 * Reads JWT from query params, sends it to the opener window via postMessage,
 * and closes itself.
 */
export default function AuthCallbackPage() {
  const searchParams = useSearchParams();

  useEffect(() => {
    const jwt = searchParams.get("jwt");
    const email = searchParams.get("email");

    if (window.opener && jwt) {
      window.opener.postMessage(
        { type: "GMAIL_AUTH_SUCCESS", jwt, email },
        window.location.origin,
      );
      window.close();
    }
  }, [searchParams]);

  return (
    <div className="flex h-screen items-center justify-center">
      <p className="text-muted-foreground">Authorizing... this window will close automatically.</p>
    </div>
  );
}
