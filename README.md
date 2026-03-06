# ColdReach AI

**AI-powered cold email outreach that automates research, contact discovery, and personalized email generation.**

---

## Overview

Connecting with startups and professionals is time-consuming — researching companies, finding the right person, and writing personalized outreach takes hours. Most "AI outreach" tools solve this by blasting generic templates.

ColdReach AI takes the opposite approach: it automates the research and writing while keeping every message specific, relevant, and human. The system scrapes company data, discovers contacts via Hunter.io, ranks the best-fit person by role and company size, and generates a personalized cold email using your resume and a customizable template — all through a single API call.

Currently, email generation uses a **template-based system** with a two-pass placeholder fill (deterministic + GPT contextual). ML-based personalization scoring is planned for a future release.

---

## How It Works

1. **Upload your resume (once per session)**
   - Upload a PDF resume to `/resume/upload`
   - The system extracts structured data: name, email, skills, experience, education, LinkedIn, GitHub
   - Stored in-memory with a `resume_id` for reuse across multiple generations

2. **Provide a company URL and email template**
   - POST to `/scrape/generate` with the company URL, your `resume_id`, and an email template containing placeholders
   - The system scrapes the company website (title, meta description, headings, keywords)

3. **Contact discovery and ranking**
   - Hunter.io Domain Search returns up to 10 contacts for the company
   - Company size is detected and a role-ranking strategy is applied:
     - **Small (1-10):** Prioritizes founders, CTOs, technical co-founders
     - **Mid (11-50):** Prioritizes VPs of Engineering, tech leads, CTOs
     - **Large (50+):** Prioritizes recruiters, hiring managers, engineering managers
   - The best-fit contact is selected automatically

4. **Two-pass email generation**
   - **Pass 1 (Deterministic):** Fills fixed placeholders — `[Company Name]`, `[First Name]`, `[Sender Name]`, `[LinkedIn]`, `[GitHub]`
   - **Pass 2 (GPT):** Fills contextual placeholders — `[specific company detail]`, `[company focus area]`, `[resume highlights]` — using scraped company data and your resume as context

5. **SES-ready response**
   - Returns a structured email object with subject, body, recipient info, contact details (name, title, seniority, confidence), and company metadata — ready to plug into a sending service

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| **FastAPI** | REST API framework |
| **Uvicorn** | ASGI server |
| **BeautifulSoup4** | Web scraping (company websites) |
| **pdfplumber** | PDF resume text extraction and parsing |
| **OpenAI API** | GPT-powered contextual placeholder filling |
| **Hunter.io API** | Contact discovery and domain search |
| **python-dotenv** | Environment variable management |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/scrape/` | GET | Scrape a company website (title, meta, keywords) |
| `/scrape/generate` | POST | Full pipeline — scrape company, find contacts, generate email |
| `/company/find` | GET | Find and rank contacts by company name or domain |
| `/resume/upload` | POST | Upload and parse a PDF resume |

---

## Project Structure

```
ColdApproach-AI/
├── app/
│   ├── main.py                    # FastAPI app, router registration
│   ├── models/
│   │   └── schemas.py             # Pydantic request/response models
│   ├── routers/
│   │   ├── scrape.py              # Scraping + email generation endpoints
│   │   ├── contacts.py            # Hunter.io contact discovery endpoint
│   │   ├── send.py                # Email sending (stub)
│   │   └── analytics.py           # Analytics (stub)
│   ├── routes/
│   │   └── resume_route.py        # Resume upload + parsing endpoint
│   ├── services/                  # Service layer (future providers)
│   └── utils/
│       ├── generate.py            # Two-pass email generation engine
│       ├── hunter_client.py       # Hunter.io API client
│       ├── scraper.py             # Website scraping + keyword extraction
│       ├── resume_parser.py       # PDF parsing + structured data extraction
│       ├── resume_store.py        # In-memory resume storage (UUID-keyed)
│       └── company_analyzer.py    # Company size analysis + role scoring
├── requirements.txt
├── .env                           # API keys (OPENAI_API_KEY, HUNTER_API_KEY)
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- OpenAI API key
- Hunter.io API key

### Setup

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
# Add your OPENAI_API_KEY and HUNTER_API_KEY to .env

# Run the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

## Future Implementations

- **ML Personalization Scoring** — TF-IDF + Logistic Regression model to score generated emails on specificity and relevance; emails below threshold trigger automatic regeneration
- **Email Sending** — Hybrid Gmail API + Amazon SES provider with automatic domain-based routing, OAuth2 for Gmail users, and EventBridge scheduling for delayed sends
- **Data Analytics & Tracking** — Track open rates, reply rates, response latency, and personalization scores; visualize performance trends and optimize outreach strategy
- **React Frontend** — User interface for resume upload, email review, template management, and analytics dashboard
- **Batch Processing** — SQS-based queue for bulk outreach: submit multiple company URLs, generate and send emails asynchronously
