# 🧠 ColdReach AI

**AI-powered outreach that values quality over quantity.**  
ColdReach AI helps students, job seekers, and developers connect more effectively with **startups and professionals** by crafting authentic, personalized cold emails.  
The system automatically scrapes company and user data, finds contact candidates using the Hunter API, ranks the best contact by role-fit, and uses a lightweight ML model to ensure every message feels specific, relevant, and human before it’s ever sent.

---

## 🚀 Overview

Connecting with startups and professionals can be difficult — researching companies, finding the right person, and writing personalized outreach messages takes hours.  
Most “AI outreach” tools solve this by blasting generic templates.  
ColdReach AI takes the opposite approach: it **automates the research and writing**, but adds an **ML quality gate** and **real contact discovery** to ensure every message is thoughtful, targeted, and worth sending.

---

## 🔍 How It Works

1. **User uploads their profile once:**
   - Resume (PDF)
   - LinkedIn URL
   - GitHub URL  
   ColdReach scrapes and summarizes these sources to understand the user’s skills, projects, and interests.  
   This user profile is stored securely (e.g., in AWS S3 or a database) and reused for future generations unless the user requests an update.

2. **User enters a company name or company link:**  
   - ColdReach scrapes the company’s website (“About” page, meta tags, key paragraphs).  
   - Summarizes what the company does and extracts relevant keywords.

3. **Hunter API integration:**  
   - ColdReach calls Hunter Domain Search and fetches up to 10 contact candidates for that company.  
   - It evaluates titles/roles using company-size strategy (`1-10`, `11-50`, `50+`) and selects the best-fit candidate.
   - The response includes the top candidates (with roles and emails) plus a `best_contact` recommendation.

4. **GPT-4 generates a draft:**  
   - Using the user’s profile + company summary + contact info, GPT creates a short, personalized cold email connecting the user’s experience to the company’s work.

5. **ML personalization scoring:**  
   - A TF-IDF + Logistic Regression model evaluates how specific, relevant, and personal the draft is.  
   - If the score is below a set threshold, ColdReach regenerates or refines the email.

6. **Send and track:**  
   - Once the draft passes the quality check, ColdReach sends it via **AWS SES**.  
   - Every email is logged (company, contact, score, and status) for analytics and improvement.

---

## 🧰 Technologies Used

| Layer | Tools | Purpose |
|-------|-------|----------|
| **Backend** | **FastAPI (Python)** | Core API endpoints (scraping, generation, scoring, sending) |
| **AI Generation** | **OpenAI GPT-4 API** | Create contextual, high-quality email drafts |
| **Machine Learning** | **scikit-learn (TF-IDF + Logistic Regression)** | Evaluate personalization quality |
| **User Data Scraping** | **BeautifulSoup4, pdfminer, OpenAI summarization** | Extract profile info from resume, LinkedIn, and GitHub |
| **Company Data Scraping** | **requests**, **BeautifulSoup4** | Summarize company content for GPT context |
| **Contact Discovery** | **Hunter.io API** | Find contact candidates and select the best-fit person by role |
| **Cloud & Infrastructure** | **AWS SES**, **S3**, **IAM** | Send emails, store user data securely |
| **Frontend** | **React + Tailwind CSS** | Simple interface for inputs, review, and analytics |
| **Data & Tracking** | **pandas**, **CSV** → *Google Sheets or PostgreSQL (future)* | Log emails, scores, and statuses |
| **Visualization** | **Chart.js / Recharts** | Analytics and performance insights |

---

## 🧩 Personalization Model

ColdReach’s ML model acts as a **content gatekeeper** — it ensures that generated emails are specific, relevant, and human-like.

It distinguishes between:
- ✅ **Personalized:** Mentions the company name or project, relates the sender’s background to their work, or references something factual.  
- ❌ **Generic:** Repetitive, vague, or sounds like a template.

Using TF-IDF text embeddings and Logistic Regression, the model produces a **personalization score (0–1)**.  
Emails below the set threshold (default 0.6) trigger a regeneration loop until the quality bar is met.

---

## ☁️ System Flow

User Uploads (Resume, LinkedIn, GitHub)  
 ↓  
Scraper → Build & Cache User Profile (store in S3/DB)  
 ↓  
User Enters Company Name or URL  
 ↓  
Scraper → Extract & Summarize Company Info  
 ↓  
Hunter API → Fetch up to 10 Candidate Contacts  
 ↓  
Role Ranking by Company Size → Choose Best Candidate  
 ↓  
GPT-4 → Generate Personalized Email  
 ↓  
ML Model → Score Personalization  
 ↓  
If score < threshold → Refine Draft  
If score ≥ threshold → Send via AWS SES  
 ↓  
Tracker → Log to CSV / Database for Analytics  

---

## 📊 Analytics & Insights

ColdReach tracks each email’s:
- Personalization score  
- Contact role and industry  
- Status (Sent, Opened, Replied, No Response)  
- Timestamps and response latency  

### From these metrics, the dashboard visualizes:
- Reply rate and open rate trends  
- Score vs. reply rate correlation  
- Top-performing industries and roles  
- Optimal send times and average response times  

### How it helps:
- **Users** see what kinds of messages and targets work best.  
- **You** (the developer) can retrain your ML model using real feedback.  
- **Future versions** can predict reply likelihood based on past data.

---

## 📊 Example Use Case

A student uploads their resume, LinkedIn, and GitHub once.  
They paste `https://clearcutar.com` into ColdReach.  
The app scrapes that ClearCutAR builds AR imaging software for surgical wound care.  
Hunter returns up to 10 likely contacts and ColdReach ranks “Lisa Chen — CTO” as the best fit.  
The response includes all fetched candidates and a best-contact recommendation for outreach.  
GPT writes:  

> “Hi Lisa, I loved your team’s work on AR imaging at ClearCutAR — I recently built a project that uses AI for real-time image processing…”  

The ML model scores it **0.84** → passes → ColdReach sends via **AWS SES**.  
The system logs: company, contact, email text, personalization score, and send status for analytics.

---

## ☁️ Summary

ColdReach AI blends **AI generation**, **ML evaluation**, **Hunter-based contact discovery**, and **cloud automation** to make outreach smarter, faster, and more meaningful.  
It empowers users to **connect with startups and professionals** through thoughtful, personalized communication — not spam.
