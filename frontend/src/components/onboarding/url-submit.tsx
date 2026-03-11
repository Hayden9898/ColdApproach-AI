"use client";

import { useState, useMemo, KeyboardEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  X,
  Loader2,
  Check,
  AlertCircle,
  Send,
  Clock,
  Globe,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/store/app-store";
import { useBatchPolling } from "@/hooks/use-batch-polling";
import { slideUp, DURATION } from "@/lib/animations";
import type { BatchUrlResult } from "@/types/api";

const BATCH_LIMIT = 20;

interface UrlSubmitProps {
  onBack: () => void;
}

function extractDomain(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function toLocalDateStr(date: Date): string {
  const y = date.getFullYear();
  const m = (date.getMonth() + 1).toString().padStart(2, "0");
  const d = date.getDate().toString().padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function buildDayOptions(): { label: string; value: string }[] {
  const options: { label: string; value: string }[] = [];
  const now = new Date();

  for (let i = 0; i < 7; i++) {
    const date = new Date(now);
    date.setDate(date.getDate() + i);
    const dateStr = toLocalDateStr(date);

    let label: string;
    if (i === 0) label = "Today";
    else if (i === 1) label = "Tomorrow";
    else {
      label = date.toLocaleDateString("en-US", {
        weekday: "long",
        month: "short",
        day: "numeric",
      });
    }

    options.push({ label, value: dateStr });
  }

  return options;
}

function buildTimeSlots(): { label: string; value: string }[] {
  const slots: { label: string; value: string }[] = [];
  for (let h = 0; h < 24; h++) {
    for (const m of [0, 30]) {
      const hour12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
      const period = h < 12 ? "AM" : "PM";
      const label = `${hour12}:${m.toString().padStart(2, "0")} ${period}`;
      const value = `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}`;
      slots.push({ label, value });
    }
  }
  return slots;
}

function buildSendAt(day: string, time: string): string | undefined {
  if (!day || !time) return undefined;
  return new Date(`${day}T${time}:00`).toISOString();
}

function isScheduleTooSoon(day: string, time: string): boolean {
  if (!day || !time) return false;
  const scheduled = new Date(`${day}T${time}:00`);
  const minTime = new Date(Date.now() + 60 * 60 * 1000);
  return scheduled < minTime;
}

function StatusIcon({ status }: { status: BatchUrlResult["status"] }) {
  switch (status) {
    case "queued":
    case "processing":
      return <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />;
    case "sent":
    case "scheduled":
      return <Check className="h-3.5 w-3.5 text-green-500" />;
    case "failed":
      return <X className="h-3.5 w-3.5 text-destructive" />;
  }
}

export function UrlSubmit({ onBack }: UrlSubmitProps) {
  const batchJobId = useAppStore((s) => s.batchJobId);
  const completeOnboarding = useAppStore((s) => s.completeOnboarding);

  const { submitBatch, batchData, isSubmitting, isPolling, reset, submitError } =
    useBatchPolling(batchJobId);

  // URL input state
  const [urls, setUrls] = useState<string[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [inputError, setInputError] = useState<string | null>(null);

  // Send mode state
  const [scheduleMode, setScheduleMode] = useState(false);
  const [scheduleDay, setScheduleDay] = useState("");
  const [scheduleTime, setScheduleTime] = useState("09:00");

  const dayOptions = useMemo(() => buildDayOptions(), []);
  const timeSlots = useMemo(() => buildTimeSlots(), []);

  // Live schedule validation
  const scheduleTooSoon = useMemo(
    () => scheduleMode && isScheduleTooSoon(scheduleDay, scheduleTime),
    [scheduleMode, scheduleDay, scheduleTime],
  );

  // Determine phase
  const batchStatus = batchData.data;
  const isComplete = batchStatus?.status === "completed";
  const isProcessing = !!batchJobId && !isComplete;
  const phase: "input" | "processing" | "complete" =
    isComplete ? "complete" : isProcessing ? "processing" : "input";

  const handleAddUrl = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== "Enter") return;
    e.preventDefault();

    let url = inputValue.trim();
    if (!url) return;

    // Auto-prepend https:// for bare domains (e.g. "company.com")
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      url = `https://${url}`;
    }

    try {
      new URL(url);
    } catch {
      setInputError("Invalid URL format");
      return;
    }

    // Check duplicates
    if (urls.includes(url)) {
      setInputError("URL already added");
      return;
    }

    // Check limit
    if (urls.length >= BATCH_LIMIT) {
      setInputError(`Maximum ${BATCH_LIMIT} URLs`);
      return;
    }

    setUrls((prev) => [...prev, url]);
    setInputValue("");
    setInputError(null);
  };

  const handleRemoveUrl = (url: string) => {
    setUrls((prev) => prev.filter((u) => u !== url));
  };

  const handleSubmit = () => {
    if (urls.length === 0) return;

    const sendAt = scheduleMode
      ? buildSendAt(scheduleDay, scheduleTime)
      : undefined;

    // Validate schedule time is at least 1 hour from now
    if (scheduleMode && sendAt) {
      const scheduled = new Date(sendAt);
      const minTime = new Date(Date.now() + 60 * 60 * 1000);
      if (scheduled < minTime) {
        setInputError("Schedule time must be at least 1 hour from now");
        return;
      }
    }

    submitBatch.mutate(
      { urls, sendAt },
      {
        onSuccess: () => {
          completeOnboarding();
        },
      },
    );
  };

  const handleSubmitAnother = () => {
    reset();
    setUrls([]);
    setInputValue("");
    setInputError(null);
  };

  // Compute summary for complete phase
  const successCount = batchStatus?.completed ?? 0;
  const failedCount = batchStatus?.failed ?? 0;
  const totalCount = batchStatus?.total ?? 0;
  const hasScheduled =
    batchStatus?.results &&
    Object.values(batchStatus.results).some((r) => r.status === "scheduled");
  const successVerb = hasScheduled ? "scheduled" : "sent";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold tracking-tight">
          {phase === "complete"
            ? "Batch complete"
            : phase === "processing"
              ? "Processing..."
              : "Submit company URLs"}
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          {phase === "complete"
            ? `Successfully ${successVerb} ${successCount} of ${totalCount} email${totalCount !== 1 ? "s" : ""}.${failedCount > 0 ? ` ${failedCount} failed.` : ""}`
            : phase === "processing"
              ? "Scraping, finding contacts, and generating emails."
              : "Add company URLs one at a time. Press Enter to add each URL."}
        </p>
      </div>

      {/* Send mode toggle — visible in input and complete phases */}
      {phase !== "processing" && (
        <div className="space-y-3">
          <div className="flex gap-1 rounded-md border border-border p-0.5 w-fit">
            <button
              type="button"
              onClick={() => setScheduleMode(false)}
              className={cn(
                "flex items-center gap-1.5 rounded-sm px-3 py-1.5 text-xs font-medium transition-colors",
                !scheduleMode
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              <Send className="h-3 w-3" />
              Send now
            </button>
            <button
              type="button"
              onClick={() => {
                setScheduleMode(true);
                if (!scheduleDay) setScheduleDay(dayOptions[0].value);
              }}
              className={cn(
                "flex items-center gap-1.5 rounded-sm px-3 py-1.5 text-xs font-medium transition-colors",
                scheduleMode
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              <Clock className="h-3 w-3" />
              Schedule for later
            </button>
          </div>

          <AnimatePresence>
            {scheduleMode && (
              <motion.div
                variants={slideUp}
                initial="initial"
                animate="animate"
                exit="exit"
                transition={{ duration: DURATION.fast }}
                className="space-y-3"
              >
                <div className="flex gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs text-muted-foreground">Day</label>
                    <Select value={scheduleDay} onValueChange={setScheduleDay}>
                      <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="Select day" />
                      </SelectTrigger>
                      <SelectContent>
                        {dayOptions.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs text-muted-foreground">Time</label>
                    <Select value={scheduleTime} onValueChange={setScheduleTime}>
                      <SelectTrigger className="w-[130px]">
                        <SelectValue placeholder="Select time" />
                      </SelectTrigger>
                      <SelectContent>
                        {timeSlots.map((slot) => (
                          <SelectItem key={slot.value} value={slot.value}>
                            {slot.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {scheduleTooSoon && (
                  <div className="flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/5 p-2.5">
                    <AlertCircle className="h-3.5 w-3.5 text-amber-500 shrink-0 mt-0.5" />
                    <p className="text-xs text-amber-600 dark:text-amber-400">
                      Choose a time at least 1 hour from now.
                    </p>
                  </div>
                )}

                <div className="flex items-start gap-2 rounded-md border border-border bg-secondary/30 p-2.5">
                  <AlertCircle className="h-3.5 w-3.5 text-muted-foreground shrink-0 mt-0.5" />
                  <p className="text-xs text-muted-foreground">
                    Scheduled emails will appear as drafts in your Gmail until
                    the send time. You can review or cancel them from Gmail.
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Phase A: URL Input */}
      {phase === "input" && (
        <div className="space-y-3">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs text-muted-foreground">Company URL</label>
              <span className="text-xs font-mono text-muted-foreground">
                {urls.length} / {BATCH_LIMIT}
              </span>
            </div>
            <Input
              value={inputValue}
              onChange={(e) => {
                setInputValue(e.target.value);
                if (inputError) setInputError(null);
              }}
              onKeyDown={handleAddUrl}
              placeholder="https://company.com"
              className="font-mono text-sm"
              disabled={urls.length >= BATCH_LIMIT}
            />
            {inputError && (
              <p className="text-xs text-destructive">{inputError}</p>
            )}
          </div>

          {/* URL list */}
          {urls.length > 0 && (
            <div className="border border-border rounded-lg divide-y divide-border">
              <AnimatePresence initial={false}>
                {urls.map((url) => (
                  <motion.div
                    key={url}
                    variants={slideUp}
                    initial="initial"
                    animate="animate"
                    exit="exit"
                    transition={{ duration: DURATION.fast }}
                    className="flex items-center justify-between px-3 py-2"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <Globe className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                      <span className="text-sm font-mono truncate">
                        {extractDomain(url)}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemoveUrl(url)}
                      className="text-muted-foreground hover:text-foreground transition-colors shrink-0 ml-2"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}

          {/* Submit error */}
          {submitError && (
            <div className="flex items-start gap-2">
              <AlertCircle className="h-3.5 w-3.5 text-destructive shrink-0 mt-0.5" />
              <p className="text-xs text-destructive">{submitError}</p>
            </div>
          )}
        </div>
      )}

      {/* Phase B & C: Results list */}
      {(phase === "processing" || phase === "complete") && batchStatus && (
        <div className="space-y-3">
          {/* Progress counter */}
          {phase === "processing" && (
            <div className="flex items-center gap-2">
              <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
              <span className="text-xs font-mono text-muted-foreground">
                {batchStatus.completed + batchStatus.failed} / {batchStatus.total} completed
              </span>
            </div>
          )}

          {/* Per-URL results */}
          <div className="border border-border rounded-lg divide-y divide-border">
            {Object.entries(batchStatus.results).map(([url, result]) => (
              <div key={url} className="px-3 py-2.5 space-y-1">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 min-w-0">
                    <StatusIcon status={result.status} />
                    <span className="text-sm font-mono truncate">
                      {extractDomain(url)}
                    </span>
                  </div>
                  <span
                    className={cn(
                      "text-xs shrink-0 ml-2",
                      result.status === "sent" || result.status === "scheduled"
                        ? "text-green-600 dark:text-green-400"
                        : result.status === "failed"
                          ? "text-destructive"
                          : "text-muted-foreground",
                    )}
                  >
                    {result.status}
                  </span>
                </div>

                {/* Contact info for completed */}
                {(result.status === "sent" || result.status === "scheduled") &&
                  result.contact && (
                    <div className="flex items-center gap-2 pl-6">
                      <p className="text-xs text-muted-foreground">
                        {result.contact.name}
                        {result.contact.email && ` · ${result.contact.email}`}
                      </p>
                      {result.contact.title && (
                        <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-teal-500/10 text-teal-400">
                          {result.contact.title}
                        </span>
                      )}
                    </div>
                  )}

                {/* Error for failed */}
                {result.status === "failed" && result.error && (
                  <p className="text-xs text-destructive pl-6">
                    {result.error}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between">
        {phase === "processing" ? (
          <div />
        ) : (
          <Button
            onClick={phase === "complete" ? onBack : onBack}
            variant="ghost"
            size="sm"
            className="gap-1.5 hover:bg-transparent hover:text-primary dark:hover:bg-transparent"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            {phase === "complete" ? "Back to template" : "Back"}
          </Button>
        )}

        {phase === "input" && (
          <Button
            onClick={handleSubmit}
            size="sm"
            disabled={urls.length === 0 || isSubmitting || scheduleTooSoon}
            className="gap-1.5"
          >
            {isSubmitting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : scheduleMode ? (
              <Clock className="h-3.5 w-3.5" />
            ) : (
              <Send className="h-3.5 w-3.5" />
            )}
            {isSubmitting
              ? "Submitting..."
              : scheduleMode
                ? "Schedule"
                : "Submit"}
          </Button>
        )}

        {phase === "complete" && (
          <Button
            onClick={handleSubmitAnother}
            size="sm"
            className="gap-1.5"
          >
            <Send className="h-3.5 w-3.5" />
            Submit another batch
          </Button>
        )}
      </div>
    </div>
  );
}
