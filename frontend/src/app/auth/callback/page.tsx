"use client";

import { useEffect } from "react";

/**
 * OAuth callback landing page — opened inside a popup/tab by startAuth().
 * Sends a postMessage to the opener window and closes itself.
 */
export default function AuthCallbackPage() {
  useEffect(() => {
    if (window.opener) {
      window.opener.postMessage(
        { type: "GMAIL_AUTH_SUCCESS" },
        window.location.origin,
      );
      window.close();
    }
  }, []);

  return (
    <div className="flex h-screen items-center justify-center">
      <p className="text-muted-foreground">Authorizing… this window will close automatically.</p>
    </div>
  );
}
