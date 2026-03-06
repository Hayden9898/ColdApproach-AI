"use client";

import { useState, useRef, useEffect } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { FileText, Loader2 } from "lucide-react";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

interface PdfViewerProps {
  src: string;
}

export function PdfViewer({ src }: PdfViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState<number>(0);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) setContainerWidth(entry.contentRect.width);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 mb-2">
        <FileText className="h-3.5 w-3.5 text-muted-foreground" />
        <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          PDF Preview
        </p>
      </div>
      <div
        ref={containerRef}
        className="rounded-lg border border-border overflow-hidden bg-card"
      >
        <Document
          file={src}
          onLoadSuccess={() => {}}
          loading={
            <div className="flex items-center justify-center h-[380px] gap-2">
              <Loader2 className="h-5 w-5 text-primary animate-spin" />
              <span className="text-sm text-muted-foreground">
                Loading PDF...
              </span>
            </div>
          }
          error={
            <div className="flex flex-col items-center justify-center h-[380px] gap-2 p-6">
              <FileText className="h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground text-center">
                Could not render PDF.
              </p>
              <a
                href={src}
                download="resume.pdf"
                className="text-xs text-primary hover:underline"
              >
                Download instead
              </a>
            </div>
          }
        >
          <Page
            pageNumber={1}
            width={containerWidth > 0 ? containerWidth : undefined}
            renderAnnotationLayer={false}
            renderTextLayer={false}
          />
        </Document>
      </div>
    </div>
  );
}
