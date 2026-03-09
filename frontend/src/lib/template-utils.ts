import type { ResumeProfile } from "@/types/api";
import { PLACEHOLDERS, MOCK_PREVIEW_DATA } from "@/lib/constants";

export interface Segment {
  text: string;
  isContextual: boolean;
}

const CONTEXTUAL_TOKENS: string[] = PLACEHOLDERS.contextual.map((p) => p.token);

/**
 * Replace all placeholder tokens in a template with values from a data map.
 */
export function replacePlaceholders(
  template: string,
  data: Record<string, string>,
): string {
  let result = template;
  for (const [token, value] of Object.entries(data)) {
    result = result.replaceAll(token, value);
  }
  return result;
}

/**
 * Build a preview data map by merging mock data with real user data where available.
 */
export function getPreviewData(
  resumeProfile: ResumeProfile | null,
  linkedinUrl: string,
  githubUrl: string,
): Record<string, string> {
  const data = { ...MOCK_PREVIEW_DATA };

  if (resumeProfile?.name) {
    data["[Sender Name]"] = resumeProfile.name;
  }
  if (linkedinUrl) {
    data["[LinkedIn]"] = linkedinUrl;
  }
  if (githubUrl) {
    data["[GitHub]"] = githubUrl;
  }

  return data;
}

/**
 * Split a template into segments, marking which parts are contextual (AI-filled)
 * vs deterministic/literal text. This lets the preview style them differently.
 */
export function segmentPreviewText(
  template: string,
  data: Record<string, string>,
): Segment[] {
  // Build a regex that matches any placeholder token in the template
  const allTokens = Object.keys(data);
  if (allTokens.length === 0) {
    return [{ text: template, isContextual: false }];
  }

  // Escape special regex chars in tokens, then join with |
  const escaped = allTokens.map((t) =>
    t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
  );
  const pattern = new RegExp(`(${escaped.join("|")})`, "g");

  const segments: Segment[] = [];
  let lastIndex = 0;

  for (const match of template.matchAll(pattern)) {
    const token = match[0];
    const start = match.index!;

    // Add literal text before this match
    if (start > lastIndex) {
      segments.push({ text: template.slice(lastIndex, start), isContextual: false });
    }

    // Add the replaced value, tagged as contextual or not
    const replacement = data[token] ?? token;
    const isContextual = CONTEXTUAL_TOKENS.includes(token);
    segments.push({ text: replacement, isContextual });

    lastIndex = start + token.length;
  }

  // Add remaining text after the last match
  if (lastIndex < template.length) {
    segments.push({ text: template.slice(lastIndex), isContextual: false });
  }

  return segments;
}
