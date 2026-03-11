"use client";

import DOMPurify from "dompurify";
import { Mail } from "lucide-react";
import { useAppStore } from "@/store/app-store";
import {
  replacePlaceholders,
  getPreviewData,
  resolvePreviewHtml,
} from "@/lib/template-utils";

export function EmailPreview() {
  const draftTemplate = useAppStore((s) => s.draftTemplate);
  const draftSubjectTemplate = useAppStore((s) => s.draftSubjectTemplate);
  const resumeProfile = useAppStore((s) => s.resumeProfile);
  const linkedinUrl = useAppStore((s) => s.linkedinUrl);
  const githubUrl = useAppStore((s) => s.githubUrl);
  const fromEmail = useAppStore((s) => s.fromEmail);

  const previewData = getPreviewData(resumeProfile, linkedinUrl, githubUrl);
  const senderName = resumeProfile?.name ?? "You";

  const resolvedSubject = replacePlaceholders(draftSubjectTemplate, previewData);
  const rawPreviewHtml = resolvePreviewHtml(draftTemplate, previewData);
  const sanitizedHtml = DOMPurify.sanitize(rawPreviewHtml, {
    ALLOWED_TAGS: [
      "p", "br", "strong", "em", "u", "a", "ul", "ol", "li", "span",
    ],
    ALLOWED_ATTR: ["href", "target", "rel", "class", "style"],
  });

  const hasContent = draftTemplate.replace(/<[^>]*>/g, "").trim().length > 0;

  return (
    <div className="flex flex-col min-h-0 h-full">
      <div className="flex-1 min-h-0 rounded-lg border border-border overflow-hidden bg-card flex flex-col">
        {/* Email header */}
        <div className="p-4 space-y-1.5 border-b border-border bg-secondary/30 shrink-0">
          <div className="flex items-center gap-2 mb-2">
            <Mail className="h-3.5 w-3.5 text-muted-foreground" />
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              Email preview
            </p>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-xs text-muted-foreground w-14 shrink-0">From</span>
            <span className="text-sm font-mono truncate">
              {senderName} &lt;{fromEmail || "you@example.com"}&gt;
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-xs text-muted-foreground w-14 shrink-0">To</span>
            <span className="text-sm font-mono truncate">
              Sarah &lt;sarah@company.com&gt;
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-xs text-muted-foreground w-14 shrink-0">Subject</span>
            <span className="text-sm font-mono font-medium truncate">
              {resolvedSubject || "No subject"}
            </span>
          </div>
        </div>

        {/* Email body — rendered HTML */}
        <div className="p-4 flex-1 min-h-0 overflow-y-auto">
          {hasContent ? (
            <div
              className="email-preview-html text-sm leading-relaxed"
              dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
            />
          ) : (
            <p className="text-sm text-muted-foreground italic">
              Start typing your template to see a preview.
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-border bg-secondary/20 shrink-0">
          <p className="text-[11px] text-muted-foreground italic">
            Preview uses sample data. Actual emails will be personalized per company.
          </p>
        </div>
      </div>
    </div>
  );
}
