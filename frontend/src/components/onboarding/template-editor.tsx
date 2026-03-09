"use client";

import { useState, useEffect } from "react";
import { ArrowLeft, RotateCcw, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/store/app-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  PLACEHOLDERS,
  DEFAULT_TEMPLATE,
  DEFAULT_SUBJECT_TEMPLATE,
} from "@/lib/constants";

interface TemplateEditorProps {
  onComplete: () => void;
  onBack: () => void;
}

export function TemplateEditor({ onComplete, onBack }: TemplateEditorProps) {
  const persistedTemplate = useAppStore((s) => s.template);
  const persistedSubject = useAppStore((s) => s.subjectTemplate);
  const smoothGrammar = useAppStore((s) => s.smoothGrammar);
  const setTemplate = useAppStore((s) => s.setTemplate);
  const setSubjectTemplate = useAppStore((s) => s.setSubjectTemplate);
  const setSmoothGrammar = useAppStore((s) => s.setSmoothGrammar);
  const setDraftTemplate = useAppStore((s) => s.setDraftTemplate);
  const setDraftSubjectTemplate = useAppStore((s) => s.setDraftSubjectTemplate);

  const [subject, setSubject] = useState(persistedSubject);
  const [body, setBody] = useState(persistedTemplate);
  const [legendOpen, setLegendOpen] = useState(false);

  // Initialize drafts for the preview on mount
  useEffect(() => {
    setDraftTemplate(persistedTemplate);
    setDraftSubjectTemplate(persistedSubject);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubjectChange = (value: string) => {
    setSubject(value);
    setDraftSubjectTemplate(value);
  };

  const handleBodyChange = (value: string) => {
    setBody(value);
    setDraftTemplate(value);
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

        {/* Email body */}
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
          <Textarea
            value={body}
            onChange={(e) => handleBodyChange(e.target.value)}
            placeholder="Write your email template..."
            className="font-mono text-sm flex-1 min-h-[120px] resize-none"
            style={{ fieldSizing: "normal" } as unknown as React.CSSProperties}
          />
        </div>

        {/* Grammar smoothing toggle */}
        <div className="p-4 shrink-0">
          <div className="flex items-center justify-between gap-4">
            <div className="space-y-0.5">
              <p className="text-xs font-medium">
                Smooth grammar around placeholders
              </p>
              <p className="text-[11px] text-muted-foreground">
                AI may adjust surrounding words for natural flow
              </p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={smoothGrammar}
              onClick={() => setSmoothGrammar(!smoothGrammar)}
              className={cn(
                "relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors",
                smoothGrammar ? "bg-primary" : "bg-muted-foreground/30",
              )}
            >
              <span
                className={cn(
                  "pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow-sm transition-transform mt-0.5",
                  smoothGrammar ? "translate-x-[18px]" : "translate-x-0.5",
                )}
              />
            </button>
          </div>
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
                Use brackets like{" "}
                <code className="font-mono bg-secondary px-1 py-0.5 rounded-sm">
                  [Company Name]
                </code>{" "}
                in your template. These get filled automatically.
              </p>

              {/* Deterministic */}
              <div className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                  From your profile &amp; contacts
                </p>
                <div className="flex flex-wrap gap-2">
                  {PLACEHOLDERS.deterministic.map((p) => (
                    <span
                      key={p.token}
                      className="text-xs font-mono bg-secondary text-secondary-foreground px-1.5 py-0.5 rounded-sm"
                      title={p.description}
                    >
                      {p.token}
                    </span>
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
                    <span
                      key={p.token}
                      className="inline-flex items-center gap-1 text-xs font-mono bg-primary/10 text-primary px-1.5 py-0.5 rounded-sm"
                      title={p.description}
                    >
                      {p.token}
                      <span className="text-[10px] bg-primary/20 px-0.5 rounded-sm">
                        AI
                      </span>
                    </span>
                  ))}
                </div>
              </div>

              {/* Link embedding */}
              <div className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                  Embed links
                </p>
                <p className="text-xs text-muted-foreground">
                  Use{" "}
                  <code className="font-mono bg-secondary px-1 py-0.5 rounded-sm">
                    [title](url)
                  </code>{" "}
                  to embed a clickable link. Predefined placeholders like [LinkedIn]
                  and [GitHub] are auto-filled from your profile — no need to embed those.
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
