"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface StepIndicatorProps {
  steps: string[];
  current: number;
}

export function StepIndicator({ steps, current }: StepIndicatorProps) {
  return (
    <div className="flex items-center gap-2">
      {steps.map((label, i) => {
        const completed = i < current;
        const active = i === current;

        return (
          <div key={label} className="flex items-center gap-2">
            {i > 0 && (
              <div
                className={cn(
                  "h-px w-6",
                  completed ? "bg-primary" : "bg-border",
                )}
              />
            )}
            <div className="flex items-center gap-1.5">
              <div
                className={cn(
                  "flex h-6 w-6 items-center justify-center rounded-sm text-xs font-medium transition-colors",
                  completed && "bg-primary text-primary-foreground",
                  active && "border border-primary text-primary",
                  !completed && !active && "border border-border text-muted-foreground",
                )}
              >
                {completed ? <Check className="h-3 w-3" /> : i + 1}
              </div>
              <span
                className={cn(
                  "hidden text-xs sm:inline",
                  active ? "text-foreground font-medium" : "text-muted-foreground",
                )}
              >
                {label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
