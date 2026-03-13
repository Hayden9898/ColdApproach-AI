# 🧊 ColdApproach-AI

**AI-powered cold email outreach — from resume to sent inbox in one flow.**

Research companies. Find the right contact. Generate personalized emails. Send or schedule — all automatically.
Try it out here: [link](https://cold-approach-ai-self.vercel.app/onboarding)

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js_16-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React_19-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript_5-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS_4-06B6D4?style=flat&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![AWS](https://img.shields.io/badge/AWS-232F3E?style=flat&logo=amazon-web-services&logoColor=white)](https://aws.amazon.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)](https://openai.com/)
[![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)

---

## Overview

Connecting with startups and professionals is time-consuming — researching companies, finding the right person, and writing personalized outreach takes hours. Most "AI outreach" tools solve this by blasting generic templates.

**ColdApproach-AI takes the opposite approach.** It automates the research and writing while keeping every message specific, relevant, and human. The system scrapes company data, discovers contacts via Hunter.io, ranks the best-fit person by role and company size, and generates a personalized cold email using your resume and a customizable template — all through a guided onboarding flow or a single API call.

---

## ✨ Features

### Implemented

| Feature | Description |
|---------|-------------|
| **Resume Upload & Parsing** | Upload a PDF resume → extracts name, email, skills, experience, education, LinkedIn, GitHub |
| **Company Scraping** | Scrapes any company URL for title, meta description, headings, and keywords |
| **Smart Contact Discovery** | Hunter.io integration with role-based ranking by company size |
| **Two-Pass Email Generation** | Deterministic placeholder fill + GPT contextual generation |
| **Gmail OAuth2** | Connect your Gmail account — send emails that appear in your Sent folder |
| **Amazon SES Provider** | Custom domain email sending with domain/email verification |
| **Provider Factory** | Automatic routing — `@gmail.com` → Gmail API, custom domains → SES |
| **Batch Processing** | Submit up to 20 company URLs → SQS queue → background worker processes each |
| **Email Scheduling** | Schedule sends via AWS EventBridge Scheduler → Lambda → Gmail draft send |
| **React Frontend** | 4-step onboarding: Resume → Profile + OAuth → Template Editor → URL Submit |
| **Rich Text Template Editor** | TipTap-based editor with formatting toolbar and placeholder support |
| **JWT Authentication** | Secure user sessions with JWT tokens + API key auth for service-to-service |
| **Real-Time Batch Polling** | Live progress updates as batch emails are generated and sent |
| **Dark Mode UI** | Dark theme by default with polished shadcn/ui components |
| **Smooth Animations** | Framer Motion transitions throughout the onboarding flow |

### 🔮 Planned

| Feature | Description |
|---------|-------------|
| **ML Personalization Scoring** | TF-IDF + Logistic Regression to score email specificity — auto-regenerate below threshold |
| **Analytics Dashboard** | Track open rates, reply rates, response latency, personalization scores |
| **Persistent Database** | Replace in-memory stores with PostgreSQL for production durability |
| **Outlook Integration** | Microsoft Graph API email provider |
| **Email A/B Testing** | Generate multiple variants, track which performs best |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Next.js 16 Frontend                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Resume   │→ │ Profile  │→ │ Template │→ │  URL Submit  │   │
│  │ Upload   │  │ + OAuth  │  │ Editor   │  │  + Batch     │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────┬───────┘   │
│        Zustand (persisted) ─── React Query ─── Framer Motion   │
└───────────────────────────────────────┬─────────────────────────┘
                                        │ REST API + JWT
┌───────────────────────────────────────▼─────────────────────────┐
│                        FastAPI Backend                           │
│                                                                  │
│  ┌─────────┐   ┌──────────┐   ┌───────────┐   ┌────────────┐  │
│  │ Scraper │──▶│ Hunter   │──▶│ Generator │──▶│  Provider  │  │
│  │ (BS4)   │   │(Contacts)│   │ (GPT 2x)  │   │  Factory   │  │
│  └─────────┘   └──────────┘   └───────────┘   └─────┬──────┘  │
│                                                  ┌───┴────┐    │
│                                                  │        │    │
│                                              Gmail     SES     │
│                                              OAuth     API     │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │   Batch Worker (SQS) ──▶ process ──▶ send / schedule     │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                                │
               ┌────────────────┼────────────────┐
               ▼                ▼                ▼
        ┌────────────┐  ┌────────────┐   ┌────────────┐
        │  AWS SQS   │  │ EventBridge│   │   Lambda   │
        │  (Queue)   │  │ (Schedule) │──▶│(Send Draft)│
        └────────────┘  └────────────┘   └────────────┘
```

---

## 🔄 How It Works

### Step 1 — Upload Your Resume
Upload a PDF resume. The system extracts structured data: **name, email, skills, experience, education, LinkedIn, GitHub**. It validates the file is actually a resume (checks for sections like "Education", "Experience" and relevant keywords). Stored in-memory with a `resume_id` for reuse.

### Step 2 — Connect Gmail & Set Profile
Connect your Gmail via **OAuth2** for email sending. Add LinkedIn and GitHub URLs. The system issues a **JWT token** for authenticated API requests going forward.

### Step 3 — Customize Your Template
Write your email template in a **rich text editor** (TipTap) with formatting and placeholders like `[Company Name]`, `[First Name]`, `[specific company detail]`. Preview how it renders in real-time.

### Step 4 — Submit URLs & Send
Enter company URLs (single or batch up to 20). For each URL, the full pipeline runs:

1. **Scrape** — BeautifulSoup extracts title, meta description, headings, keywords from the company website
2. **Discover** — Hunter.io Domain Search returns up to 10 contacts for the domain
3. **Rank** — Contacts scored by role fit based on company size:
   - **Small (1–10):** Founders, CTOs, technical co-founders
   - **Mid (11–50):** VPs of Engineering, tech leads, CTOs
   - **Large (50+):** Recruiters, hiring managers, engineering managers
4. **Generate** — Two-pass email generation:
   - **Pass 1 (Deterministic):** Fills `[Company Name]`, `[First Name]`, `[Sender Name]`, `[LinkedIn]`, `[GitHub]`
   - **Pass 2 (GPT):** Fills `[specific company detail]`, `[company focus area]`, `[resume highlights]` — using scraped data + resume as context
5. **Send** — Immediate send via Gmail/SES, or schedule for later via EventBridge → Lambda

---

## 🛠️ Tech Stack

### Backend

| Technology | Purpose |
|------------|---------|
| [FastAPI](https://fastapi.tiangolo.com/) | REST API framework |
| [Uvicorn](https://www.uvicorn.org/) | ASGI server |
| [Pydantic](https://docs.pydantic.dev/) | Request/response validation |
| [OpenAI API](https://platform.openai.com/) | GPT-powered contextual email generation |
| [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) | Web scraping (company websites) |
| [pdfplumber](https://github.com/jsvine/pdfplumber) | PDF resume parsing and text extraction |
| [Hunter.io API](https://hunter.io/) | Contact discovery and domain search |
| [Google Auth + Gmail API](https://developers.google.com/gmail/api) | OAuth2 authentication and email sending |
| [boto3 (AWS SDK)](https://boto3.amazonaws.com/v1/documentation/api/latest/) | SES, SQS, EventBridge Scheduler |
| [PyJWT](https://pyjwt.readthedocs.io/) | JWT token creation and verification |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Environment variable management |

### Frontend

| Technology | Purpose |
|------------|---------|
| [Next.js 16](https://nextjs.org/) | React framework (App Router) |
| [React 19](https://react.dev/) | UI library |
| [TypeScript 5](https://www.typescriptlang.org/) | Type safety |
| [Zustand 5](https://zustand.docs.pmnd.rs/) | State management with localStorage persistence |
| [React Query 5](https://tanstack.com/query) | Server state, mutations, and polling |
| [TipTap 3](https://tiptap.dev/) | Rich text template editor |
| [Framer Motion 12](https://motion.dev/) | Animations and transitions |
| [Tailwind CSS 4](https://tailwindcss.com/) | Utility-first styling |
| [shadcn/ui + Radix](https://ui.shadcn.com/) | Accessible UI component primitives |
| [Zod 4](https://zod.dev/) | Schema validation |
| [React Hook Form](https://react-hook-form.com/) | Form management |
| [react-pdf](https://github.com/wojtekmaj/react-pdf) | PDF resume viewer |
| [react-dropzone](https://react-dropzone.js.org/) | Drag-and-drop file upload |
| [Lucide React](https://lucide.dev/) | Icon library |
| [DOMPurify](https://github.com/cure53/DOMPurify) | HTML sanitization |
| [chrono-node](https://github.com/wanasit/chrono) | Natural language date parsing |

### Infrastructure (AWS)

| Service | Purpose |
|---------|---------|
| **SES** | Email sending for custom domain senders |
| **SQS** | Message queue for batch URL processing |
| **EventBridge Scheduler** | One-time schedules for delayed email sends |
| **Lambda** | Serverless function to send Gmail drafts at scheduled time |
| **Google OAuth2** | Gmail account authentication |

---

## 📡 API Endpoints

### Resume

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/resume/upload` | POST | — | Upload PDF resume, parse and extract structured data |

### Authentication

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/gmail/login` | GET | — | Redirect to Google OAuth2 consent screen |
| `/auth/gmail/callback` | GET | — | OAuth2 callback — exchange code for tokens, issue JWT |
| `/auth/gmail/status` | GET | JWT | Check Gmail OAuth connection status |

### Scraping & Generation

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/scrape/` | GET | JWT | Scrape company website metadata |
| `/scrape/generate` | POST | JWT | Full pipeline: scrape → discover contacts → generate email |
| `/company/find` | GET | JWT | Find and rank contacts by company domain |

### Sending & Scheduling

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/send/email` | POST | JWT | Send email immediately or schedule for later |
| `/send/ses/verify` | POST | — | Request SES email address verification |
| `/send/ses/status` | GET | — | Check SES verification status |
| `/send/draft` | POST | JWT / API Key | Send a Gmail draft (used by Lambda for scheduled sends) |

### Batch Processing

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/batch/submit` | POST | JWT | Submit batch of URLs for async processing |
| `/batch/{job_id}/status` | GET | — | Poll batch job progress and results |

### Health

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/` | GET | — | Health check |

---

## 📁 Project Structure

```
ColdApproach-AI/
├── app/                                 # FastAPI Backend
│   ├── main.py                          # App init, router registration, lifespan (SQS worker)
│   ├── models/
│   │   └── schemas.py                   # Pydantic request/response models
│   ├── routers/
│   │   ├── auth.py                      # Gmail OAuth2 endpoints
│   │   ├── batch.py                     # Batch submission & status polling
│   │   ├── send.py                      # Email sending & scheduling
│   │   ├── scrape.py                    # Company scraping + email generation
│   │   ├── resume.py                    # Resume upload & parsing
│   │   ├── contacts.py                  # Contact discovery
│   │   └── analytics.py                # Analytics (stub)
│   ├── services/
│   │   ├── batch_worker.py              # Background SQS polling & processing
│   │   ├── email_provider.py            # Abstract email provider interface
│   │   ├── gmail_provider.py            # Gmail API implementation
│   │   ├── ses_provider.py              # Amazon SES implementation
│   │   ├── provider_factory.py          # Provider selection by sender domain
│   │   ├── scheduler.py                 # EventBridge Scheduler integration
│   │   └── sqs_client.py               # SQS message queue wrapper
│   └── utils/
│       ├── auth.py                      # JWT & API key verification
│       ├── jwt_manager.py               # JWT token creation/decode
│       ├── generate.py                  # Two-pass email generation engine
│       ├── scraper.py                   # Website scraping + keyword extraction
│       ├── hunter_client.py             # Hunter.io API client
│       ├── company_analyzer.py          # Company size analysis + role scoring
│       ├── resume_parser.py             # PDF parsing + structured extraction
│       ├── resume_store.py              # In-memory resume storage
│       ├── token_store.py               # In-memory OAuth token storage
│       ├── batch_store.py               # In-memory batch job tracking
│       ├── email_store.py               # Email storage utility
│       └── html_builder.py              # Markdown → inline-styled HTML email
│
├── frontend/                            # Next.js 16 Frontend
│   └── src/
│       ├── app/
│       │   ├── layout.tsx               # Root layout
│       │   ├── page.tsx                 # Home → redirects to onboarding
│       │   ├── onboarding/page.tsx      # 4-step onboarding flow
│       │   └── auth/callback/page.tsx   # Gmail OAuth callback page
│       ├── components/
│       │   ├── onboarding/
│       │   │   ├── resume-upload.tsx     # PDF dropzone + upload
│       │   │   ├── profile-setup.tsx     # Email, LinkedIn, GitHub + OAuth
│       │   │   ├── template-editor.tsx   # Email template with placeholders
│       │   │   ├── email-preview.tsx     # Generated email preview
│       │   │   ├── url-submit.tsx        # URL input + batch + send/schedule
│       │   │   ├── rich-text-editor.tsx  # TipTap rich text editor
│       │   │   ├── pdf-viewer.tsx        # Resume PDF viewer
│       │   │   └── step-indicator.tsx    # Onboarding progress indicator
│       │   ├── ui/                      # shadcn/ui primitives
│       │   └── shared/
│       │       └── logo.tsx             # App logo component
│       ├── hooks/
│       │   ├── use-resume-upload.ts      # Resume upload mutation
│       │   ├── use-email-auth.ts         # Gmail OAuth popup + verification
│       │   └── use-batch-polling.ts      # Batch submit + status polling
│       ├── lib/
│       │   ├── api.ts                   # API client (fetch wrapper + JWT)
│       │   ├── constants.ts             # Placeholders, default templates
│       │   ├── template-utils.ts        # Template parsing utilities
│       │   ├── animations.ts            # Framer Motion animation variants
│       │   └── utils.ts                 # General utilities
│       ├── types/
│       │   └── api.ts                   # TypeScript request/response types
│       ├── store/
│       │   └── app-store.ts             # Zustand store (persisted to localStorage)
│       └── providers/
│           └── query-provider.tsx       # React Query provider
│
├── lambda/
│   └── send_email_handler.py            # Lambda: send Gmail draft at scheduled time
│
├── requirements.txt                     # Python dependencies
├── .env.example                         # Environment variable template
└── README.md
```

---

## ⚠️ Production Considerations

All infrastructure is built and functional — the limitations below are **financial and verification barriers**, not technical ones. The code is production-ready; unlocking full capability requires paid tiers or approval processes.

### Gmail OAuth — Unverified App

The app uses the `gmail.compose` restricted scope (chosen over `gmail.send` because it enables the draft workaround described below). Both scopes are classified as **restricted** by Google, which means:

- Google requires **OAuth consent screen verification** and a **CASA security assessment** (~$15,000–$75,000) before the app can be used by more than 100 test users
- Until verified, Google displays a large yellow **"This app isn't verified"** warning banner when users attempt to grant access — some users may be blocked entirely
- Direct email sending works, but triggers this warning on every OAuth flow

**Workaround — Draft Mode:** Instead of sending directly, the app creates a **Gmail draft** in the user's account. The user can open their Drafts folder and send or schedule the email themselves. This is simple, reliable, and sidesteps the unverified app warning entirely.

### Email Scheduling — Render Free Tier Cold Boot

The scheduling chain works like this: **EventBridge Scheduler → Lambda (30s timeout) → HTTP call to the API**.

- Render's free tier spins down instances after inactivity. Cold boot takes **~50 seconds**
- Lambda's HTTP request timeout is **30 seconds** — shorter than the cold boot
- Result: Lambda times out before the API finishes booting → the scheduled send **fails silently**

**Fix:** A premium hosting plan (always-on instance) eliminates cold boot entirely and makes the scheduling chain reliable.

### AWS SES — Sandbox Mode

The SES provider infrastructure is fully built — email verification flow, MIME support, attachment handling, and domain-based routing all work. However:

- SES **sandbox mode** only allows sending to **pre-verified email addresses** (both sender and recipient must be verified)
- Moving to production access requires submitting a request to AWS demonstrating a legitimate use case

**Fix:** Request SES production access from AWS. The approval process is free — it just requires demonstrating that you have a valid sending use case and proper bounce/complaint handling.

### The Bottom Line

The entire infrastructure pipeline — OAuth, email providers, batch processing, scheduling — is implemented and wired up. These services work correctly in development and testing. Reaching full production capability is a matter of paid hosting, Google verification, and AWS approval — not additional engineering.

---

## 💰 Cost to Go Live

The app is fully functional in development. Going to production primarily requires **Google OAuth verification** (~$15K–$75K CASA security assessment) and a **premium hosting plan** to eliminate cold boot. AWS SES production access and API usage costs are minimal.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- API keys: [OpenAI](https://platform.openai.com/), [Hunter.io](https://hunter.io/)
- AWS account with SES, SQS, EventBridge, and Lambda configured
- Google Cloud project with Gmail API enabled and OAuth2 credentials

### Backend Setup

```bash
# Clone the repo
git clone https://github.com/your-username/ColdApproach-AI.git
cd ColdApproach-AI

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Fill in all required keys (see below)

# Run the server
uvicorn app.main:app --reload
```

API available at `http://localhost:8000` — interactive docs at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend available at `http://localhost:3000`.

### Environment Variables

```env
# Auth
JWT_SECRET=              # python -c "import secrets; print(secrets.token_urlsafe(64))"
API_KEY=                 # python -c "import secrets; print(secrets.token_urlsafe(32))"
CORS_ORIGINS=            # e.g. http://localhost:3000
FRONTEND_URL=            # e.g. http://localhost:3000

# Google OAuth2
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=     # e.g. http://localhost:8000/auth/gmail/callback

# APIs
OPENAI_API_KEY=
HUNTER_API_KEY=

# AWS
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=              # Default: ca-central-1
SQS_QUEUE_URL=
SEND_EMAIL_LAMBDA_ARN=
SCHEDULER_ROLE_ARN=

# Frontend
NEXT_PUBLIC_API_URL=     # e.g. http://localhost:8000
```

---

## 🧠 Design Decisions

| Decision | Rationale |
|----------|-----------|
| **In-memory stores** (no DB) | MVP speed — swap to PostgreSQL when persistence is needed |
| **Two-pass generation** | Deterministic pass handles known data reliably; GPT pass handles nuance |
| **Provider factory pattern** | Extensible — add Outlook, SendGrid, etc. without touching existing code |
| **Background SQS worker** | Non-blocking batch processing; scales independently from API |
| **EventBridge + Lambda** | Serverless one-time schedules — no cron jobs, no persistent workers |
| **JWT + API key dual auth** | JWT for user sessions, API key for service-to-service (Lambda → API) |
| **`gmail.compose` scope** | Enables draft workaround for unverified apps; same verification cost as `gmail.send` |
| **Zustand with selective persistence** | Only persist what survives refresh (template, email, resume) — not transient UI state |

---

## 📜 License

MIT

---

<p align="center">
  Built with caffeine and too many API keys ☕
</p>
