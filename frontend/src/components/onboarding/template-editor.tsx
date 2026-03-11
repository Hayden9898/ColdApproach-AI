"use client";

import { useState, useEffect, useCallback } from "react";
import { ArrowLeft, RotateCcw, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/store/app-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { RichTextEditor } from "@/components/onboarding/rich-text-editor";
import {
  PLACEHOLDERS,
  DEFAULT_TEMPLATE,
  DEFAULT_SUBJECT_TEMPLATE,
} from "@/lib/constants";

interface TemplateEditorProps {
  onComplete: () => void;
  onBack: () => void;
}

/**
 * Convert legacy plaintext templates (from localStorage) to HTML
 * so the TipTap editor can render them properly.
 */
function ensureHtml(text: string): string {
  // Already HTML — return as-is
  if (text.trimStart().startsWith("<")) return text;
  // Convert plaintext: split on double newlines → <p>, single newlines → <br>
  return text
    .split(/\n{2,}/)
    .map((p) => `<p>${p.replace(/\n/g, "<br>")}</p>`)
    .join("");
}

export function TemplateEditor({ onComplete, onBack }: TemplateEditorProps) {
  const persistedTemplate = useAppStore((s) => s.template);
  const persistedSubject = useAppStore((s) => s.subjectTemplate);
  const setTemplate = useAppStore((s) => s.setTemplate);
  const setSubjectTemplate = useAppStore((s) => s.setSubjectTemplate);
  const setDraftTemplate = useAppStore((s) => s.setDraftTemplate);
  const setDraftSubjectTemplate = useAppStore((s) => s.setDraftSubjectTemplate);

  const [subject, setSubject] = useState(persistedSubject);
  const [body, setBody] = useState(() => ensureHtml(persistedTemplate));
  const [legendOpen, setLegendOpen] = useState(false);
  const [insertText, setInsertText] = useState<
    ((text: string) => void) | null
  >(null);

  // Initialize drafts for the preview on mount
  useEffect(() => {
    setDraftTemplate(ensureHtml(persistedTemplate));
    setDraftSubjectTemplate(persistedSubject);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubjectChange = (value: string) => {
    setSubject(value);
    setDraftSubjectTemplate(value);
  };

  const handleBodyChange = (html: string) => {
    setBody(html);
    setDraftTemplate(html);
  };

  const handleReset = () => {
    setSubject(DEFAULT_SUBJECT_TEMPLATE);
    setBody(DEFAULT_TEMPLATE);
    setDraftSubjectTemplate(DEFAULT_SUBJECT_TEMPLATE);
    setDraftTemplate(DEFAULT_TEMPLATE);
  };

  const handleContinue = () => {
    setTemplate(body);
    setSubjectTemplate(subject);
    onComplete();
  };

  // Store the insert function from the editor
  const handleEditorReady = useCallback(
    (fn: (text: string) => void) => {
      setInsertText(() => fn);
    },
    [],
  );

  return (
    <div className="flex flex-col min-h-0 h-full">
      <div className="flex-1 min-h-0 border border-border bg-card rounded-lg divide-y divide-border flex flex-col">
        {/* Subject line */}
        <div className="p-4 space-y-3 shrink-0">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Subject line
          </p>
          <Input
            value={subject}
            onChange={(e) => handleSubjectChange(e.target.value)}
            placeholder="Email subject..."
            className="font-mono text-sm"
          />
        </div>

        {/* Email body — rich text editor */}
        <div className="p-4 space-y-3 flex-1 min-h-0 flex flex-col">
          <div className="flex items-center justify-between shrink-0">
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              Email body
            </p>
            <Button
              onClick={handleReset}
              variant="outline"
              size="xs"
              className="gap-1.5 hover:text-primary"
            >
              <RotateCcw className="h-3 w-3" />
              Reset
            </Button>
          </div>
          <RichTextEditor
            content={body}
            onChange={handleBodyChange}
            placeholder="Write your email template…"
            className="flex-1 min-h-[120px]"
            onReady={handleEditorReady}
          />
        </div>

        {/* Placeholder legend */}
        <div className="shrink-0 overflow-y-auto max-h-[200px]">
          <button
            onClick={() => setLegendOpen(!legendOpen)}
            className="w-full p-4 flex items-center justify-between cursor-pointer"
          >
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              Available placeholders
            </p>
            <ChevronDown
              className={cn(
                "h-3.5 w-3.5 text-muted-foreground transition-transform",
                legendOpen && "rotate-180",
              )}
            />
          </button>
          {legendOpen && (
            <div className="px-4 pb-4 space-y-4">
              <p className="text-xs text-muted-foreground">
                Click a placeholder to insert it at cursor position.
              </p>

              {/* Deterministic */}
              <div className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                  From your profile &amp; contacts
                </p>
                <div className="flex flex-wrap gap-2">
                  {PLACEHOLDERS.deterministic.map((p) => (
                    <button
                      key={p.token}
                      type="button"
                      onClick={() => insertText?.(p.token)}
                      className="text-xs font-mono bg-secondary text-secondary-foreground px-1.5 py-0.5 rounded-sm cursor-pointer hover:bg-secondary/80 hover:text-primary transition-colors"
                      title={p.description}
                    >
                      {p.token}
                    </button>
                  ))}
                </div>
              </div>

              {/* Contextual */}
              <div className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                  AI-generated
                </p>
                <div className="flex flex-wrap gap-2">
                  {PLACEHOLDERS.contextual.map((p) => (
                    <button
                      key={p.token}
                      type="button"
                      onClick={() => insertText?.(p.token)}
                      className="inline-flex items-center gap-1 text-xs font-mono bg-primary/10 text-primary px-1.5 py-0.5 rounded-sm cursor-pointer hover:bg-primary/20 transition-colors"
                      title={p.description}
                    >
                      {p.token}
                      <span className="text-[10px] bg-primary/20 px-0.5 rounded-sm">
                        AI
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Link embedding tip */}
              <div className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                  Embed links
                </p>
                <p className="text-xs text-muted-foreground">
                  Select text and click the link button in the toolbar to add a
                  hyperlink. [LinkedIn] and [GitHub] placeholders are
                  auto-filled from your profile.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-between pt-4 shrink-0">
        <Button
          onClick={onBack}
          variant="ghost"
          size="sm"
          className="gap-1.5 hover:bg-transparent hover:text-primary dark:hover:bg-transparent"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back
        </Button>
        <Button onClick={handleContinue} size="sm">
          Continue
        </Button>
      </div>
    </div>
  );
}
