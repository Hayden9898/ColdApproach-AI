"use client";

import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Link from "@tiptap/extension-link";
import Underline from "@tiptap/extension-underline";
import { TextStyle, FontSize } from "@tiptap/extension-text-style";
import Placeholder from "@tiptap/extension-placeholder";
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  List,
  ListOrdered,
  Link as LinkIcon,
  ChevronDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCallback, useEffect, useRef, useState } from "react";

/* ------------------------------------------------------------------ */
/*  Font size options                                                  */
/* ------------------------------------------------------------------ */

const FONT_SIZES = [
  { label: "Small", value: "13px" },
  { label: "Normal", value: "" },
  { label: "Large", value: "18px" },
  { label: "X-Large", value: "22px" },
] as const;

/* ------------------------------------------------------------------ */
/*  Props                                                              */
/* ------------------------------------------------------------------ */

interface RichTextEditorProps {
  content: string;
  onChange: (html: string) => void;
  placeholder?: string;
  className?: string;
  /** Called once the editor mounts — provides a function to insert text at cursor. */
  onReady?: (insertFn: (text: string) => void) => void;
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export function RichTextEditor({
  content,
  onChange,
  placeholder,
  className,
  onReady,
}: RichTextEditorProps) {
  const [sizeOpen, setSizeOpen] = useState(false);
  const sizeRef = useRef<HTMLDivElement>(null);

  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit.configure({
        heading: false,
        codeBlock: false,
        code: false,
        blockquote: false,
        horizontalRule: false,
      }),
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: "text-blue-400 underline underline-offset-2 cursor-pointer",
        },
      }),
      Underline,
      TextStyle,
      FontSize,
      Placeholder.configure({
        placeholder: placeholder || "Write your email template…",
      }),
    ],
    content,
    onUpdate: ({ editor: e }) => {
      onChange(e.getHTML());
    },
    editorProps: {
      attributes: {
        class:
          "focus:outline-none min-h-[120px] px-3 py-2 text-sm leading-relaxed",
      },
    },
  });

  // Expose insert function to parent
  useEffect(() => {
    if (editor && onReady) {
      onReady((text: string) => {
        editor.chain().focus().insertContent(text).run();
      });
    }
  }, [editor, onReady]);

  // Sync content when reset externally
  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content);
    }
  }, [content]); // eslint-disable-line react-hooks/exhaustive-deps

  // Close font size dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (sizeRef.current && !sizeRef.current.contains(e.target as Node)) {
        setSizeOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  /* ---- helpers ---- */

  const currentFontSize = (() => {
    if (!editor) return "";
    const attrs = editor.getAttributes("textStyle");
    return (attrs.fontSize as string) || "";
  })();

  const applyFontSize = useCallback(
    (size: string) => {
      if (!editor) return;
      if (!size) {
        // "Normal" — remove any custom font size
        editor.chain().focus().unsetFontSize().run();
      } else {
        editor.chain().focus().setFontSize(size).run();
      }
      setSizeOpen(false);
    },
    [editor],
  );

  const toggleLink = useCallback(() => {
    if (!editor) return;
    if (editor.isActive("link")) {
      editor.chain().focus().unsetLink().run();
      return;
    }
    const url = window.prompt("URL:");
    if (url) {
      editor
        .chain()
        .focus()
        .setLink({ href: url.startsWith("http") ? url : `https://${url}` })
        .run();
    }
  }, [editor]);

  if (!editor) return null;

  const sizeLabel =
    FONT_SIZES.find((s) => s.value === currentFontSize)?.label || "Normal";

  return (
    <div
      className={cn(
        "rounded-md overflow-hidden border border-border bg-background flex flex-col",
        className,
      )}
    >
      {/* ─── Toolbar ─── */}
      <div className="flex items-center gap-0.5 px-2 py-1.5 border-b border-border bg-secondary/30 flex-wrap">
        <ToolbarButton
          active={editor.isActive("bold")}
          onClick={() => editor.chain().focus().toggleBold().run()}
          title="Bold (Ctrl+B)"
        >
          <Bold className="h-3.5 w-3.5" />
        </ToolbarButton>

        <ToolbarButton
          active={editor.isActive("italic")}
          onClick={() => editor.chain().focus().toggleItalic().run()}
          title="Italic (Ctrl+I)"
        >
          <Italic className="h-3.5 w-3.5" />
        </ToolbarButton>

        <ToolbarButton
          active={editor.isActive("underline")}
          onClick={() => editor.chain().focus().toggleUnderline().run()}
          title="Underline (Ctrl+U)"
        >
          <UnderlineIcon className="h-3.5 w-3.5" />
        </ToolbarButton>

        <Separator />

        {/* Font size dropdown */}
        <div ref={sizeRef} className="relative">
          <button
            type="button"
            onClick={() => setSizeOpen(!sizeOpen)}
            className={cn(
              "flex items-center gap-1 px-2 h-7 text-xs rounded transition-colors",
              "text-muted-foreground hover:text-foreground hover:bg-secondary",
            )}
            title="Font size"
          >
            {sizeLabel}
            <ChevronDown className="h-3 w-3" />
          </button>
          {sizeOpen && (
            <div className="absolute top-full left-0 mt-1 bg-popover border border-border rounded-md shadow-lg z-50 py-1 min-w-[100px]">
              {FONT_SIZES.map((s) => (
                <button
                  key={s.label}
                  type="button"
                  onClick={() => applyFontSize(s.value)}
                  className={cn(
                    "w-full text-left px-3 py-1.5 text-xs transition-colors",
                    currentFontSize === s.value
                      ? "bg-primary/10 text-primary"
                      : "text-foreground hover:bg-secondary",
                  )}
                  style={s.value ? { fontSize: s.value } : undefined}
                >
                  {s.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <Separator />

        <ToolbarButton
          active={editor.isActive("bulletList")}
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          title="Bullet list"
        >
          <List className="h-3.5 w-3.5" />
        </ToolbarButton>

        <ToolbarButton
          active={editor.isActive("orderedList")}
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          title="Ordered list"
        >
          <ListOrdered className="h-3.5 w-3.5" />
        </ToolbarButton>

        <Separator />

        <ToolbarButton
          active={editor.isActive("link")}
          onClick={toggleLink}
          title="Insert link"
        >
          <LinkIcon className="h-3.5 w-3.5" />
        </ToolbarButton>
      </div>

      {/* ─── Editor content ─── */}
      <div className="flex-1 min-h-0 overflow-y-auto">
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Toolbar primitives                                                 */
/* ------------------------------------------------------------------ */

function ToolbarButton({
  active,
  onClick,
  title,
  children,
}: {
  active: boolean;
  onClick: () => void;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      className={cn(
        "p-1.5 rounded transition-colors",
        active
          ? "bg-primary/20 text-primary"
          : "text-muted-foreground hover:text-foreground hover:bg-secondary",
      )}
    >
      {children}
    </button>
  );
}

function Separator() {
  return <div className="w-px h-5 bg-border/50 mx-1" />;
}
