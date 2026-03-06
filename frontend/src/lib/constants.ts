export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const PLACEHOLDERS = {
  deterministic: [
    { token: "[Company Name]", description: "Company name from Hunter API" },
    { token: "[First Name]", description: "Contact's first name" },
    { token: "[Sender Name]", description: "Your name from resume" },
    { token: "[LinkedIn]", description: "Your LinkedIn URL" },
    { token: "[GitHub]", description: "Your GitHub URL" },
  ],
  contextual: [
    { token: "[specific company detail]", description: "GPT infers from website" },
    { token: "[company focus area]", description: "GPT identifies from keywords" },
    {
      token: "[resume highlights - bullet points]",
      description: "GPT matches your skills to company",
    },
  ],
} as const;

export const DEFAULT_TEMPLATE = `Hi [First Name],

I came across [Company Name] and was impressed by [specific company detail]. Your work in [company focus area] aligns closely with my experience in software engineering.

[resume highlights - bullet points]

I'd love to connect and explore how I could contribute to your team. Would you be open to a brief chat?

Best,
[Sender Name]
[LinkedIn]
[GitHub]`;

export const DEFAULT_SUBJECT_TEMPLATE =
  "Exploring opportunities at [Company Name]";

export const MOCK_PREVIEW_DATA: Record<string, string> = {
  "[Company Name]": "Stripe",
  "[First Name]": "Sarah",
  "[Sender Name]": "You",
  "[LinkedIn]": "linkedin.com/in/yourprofile",
  "[GitHub]": "github.com/yourprofile",
  "[specific company detail]":
    "your recent expansion of the payments infrastructure API",
  "[company focus area]": "fintech and developer tooling",
  "[resume highlights - bullet points]":
    "- Built distributed systems handling 10M+ daily transactions\n- Led API redesign reducing latency by 40%\n- Full-stack experience with React, Python, and AWS",
};
