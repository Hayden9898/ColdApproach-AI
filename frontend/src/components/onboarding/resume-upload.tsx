"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, AlertCircle, Loader2, ArrowLeft, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { useResumeUpload } from "@/hooks/use-resume-upload";
import { useAppStore } from "@/store/app-store";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";

interface ResumeUploadProps {
  onComplete: () => void;
  onBack: () => void;
}

export function ResumeUpload({ onComplete, onBack }: ResumeUploadProps) {
  const [error, setError] = useState<string | null>(null);
  const [eduOpen, setEduOpen] = useState(false);
  const resumeProfile = useAppStore((s) => s.resumeProfile);
  const upload = useResumeUpload();

  const onDrop = useCallback(
    (accepted: File[], rejected: { file: File }[]) => {
      setError(null);

      if (rejected.length > 0) {
        setError("Only PDF files are accepted.");
        return;
      }

      const file = accepted[0];
      if (!file) return;

      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setError("Only PDF files are accepted.");
        return;
      }

      const reader = new FileReader();
      reader.onload = () => {
        useAppStore.getState().setResumePdf(reader.result as string);
      };
      reader.readAsDataURL(file);

      upload.mutate(file, {
        onError: (err) => {
          if (err instanceof ApiError) {
            setError(
              (err.data as { detail?: string })?.detail ?? "Upload failed",
            );
          } else {
            setError(err instanceof Error ? err.message : "Upload failed");
          }
        },
      });
    },
    [upload],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
    multiple: false,
  });

  const handleReplace = () => {
    useAppStore.setState({ resumeId: null, resumeProfile: null, resumePdfDataUrl: null });
    setError(null);
  };

  // Already uploaded — show full parsed resume
  if (resumeProfile && !upload.isPending) {
    return (
      <div className="flex flex-col gap-4 h-full">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-3.5 w-3.5 text-muted-foreground" />
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              Resume parsed
            </p>
          </div>
          <Button
            onClick={handleReplace}
            variant="outline"
            size="xs"
            className="gap-1.5 hover:text-primary"
          >
            <Upload className="h-3 w-3" />
            Replace
          </Button>
        </div>

        <div className="flex-1 border border-border bg-card rounded-lg divide-y divide-border">

          {/* Skills */}
          {resumeProfile.skills.length > 0 && (
            <div className="p-4">
              <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-2">
                Skills
              </p>
              <div className="flex flex-wrap gap-1.5">
                {resumeProfile.skills.slice(0, 12).map((skill) => (
                  <span
                    key={skill}
                    className="text-xs font-mono bg-secondary text-secondary-foreground px-1.5 py-0.5 rounded-sm"
                  >
                    {skill}
                  </span>
                ))}
                {resumeProfile.skills.length > 12 && (
                  <span className="text-xs font-mono text-muted-foreground px-1.5 py-0.5">
                    +{resumeProfile.skills.length - 12} more
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Experience */}
          {resumeProfile.experience.length > 0 && (
            <div className="p-4">
              <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-2">
                Experience
              </p>
              <div className="space-y-3">
                {resumeProfile.experience.map((exp, i) => (
                  <div key={i}>
                    <div className="flex items-baseline justify-between gap-2">
                      <p className="text-sm font-medium">
                        {exp.title ?? exp.company ?? "Role"}
                      </p>
                      {exp.duration && (
                        <span className="text-xs font-mono text-muted-foreground shrink-0">
                          {exp.duration}
                        </span>
                      )}
                    </div>
                    {exp.company && exp.title && (
                      <p className="text-xs text-muted-foreground">
                        {exp.company}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Projects */}
          {resumeProfile.projects?.length > 0 && (
            <div className="p-4">
              <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-2">
                Projects
              </p>
              <div className="space-y-3">
                {resumeProfile.projects.map((proj, i) => (
                  <div key={i}>
                    <div className="flex items-baseline justify-between gap-2">
                      <p className="text-sm font-medium">
                        {proj.name ?? "Project"}
                      </p>
                      {proj.duration && (
                        <span className="text-xs font-mono text-muted-foreground shrink-0">
                          {proj.duration}
                        </span>
                      )}
                    </div>
                    {proj.technologies && (
                      <p className="text-xs text-muted-foreground">
                        {proj.technologies}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Education (collapsible) */}
          {resumeProfile.education.length > 0 && (
            <div>
              <button
                onClick={() => setEduOpen(!eduOpen)}
                className="w-full p-4 flex items-center justify-between cursor-pointer"
              >
                <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                  Education
                </p>
                <ChevronDown
                  className={cn(
                    "h-3.5 w-3.5 text-muted-foreground transition-transform",
                    eduOpen && "rotate-180",
                  )}
                />
              </button>
              {eduOpen && (
                <div className="px-4 pb-4 space-y-2">
                  {resumeProfile.education.map((edu, i) => (
                    <div key={i}>
                      <p className="text-sm font-medium">
                        {edu.degree ?? edu.school ?? "Degree"}
                        {edu.field ? `, ${edu.field}` : ""}
                      </p>
                      {edu.school && edu.degree && (
                        <p className="text-xs text-muted-foreground">
                          {edu.school}
                          {edu.gpa ? ` — GPA ${edu.gpa}` : ""}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex justify-between">
          <Button onClick={onBack} variant="ghost" size="sm" className="gap-1.5 hover:bg-transparent hover:text-primary dark:hover:bg-transparent">
            <ArrowLeft className="h-3.5 w-3.5" />
            Back
          </Button>
          <Button onClick={onComplete} size="sm">
            Continue
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">
          Upload your resume
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          PDF only. We&apos;ll extract your name, skills, and experience.
        </p>
      </div>

      <div
        {...getRootProps()}
        className={cn(
          "flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed p-10 cursor-pointer transition-colors",
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-border hover:border-muted-foreground",
          upload.isPending && "pointer-events-none opacity-60",
        )}
      >
        <input {...getInputProps()} />

        {upload.isPending ? (
          <>
            <Loader2 className="h-8 w-8 text-primary animate-spin" />
            <p className="text-sm text-muted-foreground">
              Parsing resume...
            </p>
          </>
        ) : (
          <>
            <Upload
              className={cn(
                "h-8 w-8",
                isDragActive ? "text-primary" : "text-muted-foreground",
              )}
            />
            <div className="text-center">
              <p className="text-sm text-muted-foreground">
                Drop PDF here or{" "}
                <span className="text-foreground font-medium">
                  click to browse
                </span>
              </p>
            </div>
          </>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <Button onClick={onBack} variant="ghost" size="sm" className="gap-1.5 hover:bg-transparent hover:text-primary dark:hover:bg-transparent">
        <ArrowLeft className="h-3.5 w-3.5" />
        Back
      </Button>
    </div>
  );
}
