# ✉️ AI Outreach Automation System

A production-style MVP for automated personalized cold outreach. Built for freelancers, agencies, and small businesses.

---

## 🏗️ Architecture

```
ai_outreach/
├── app.py                    # Streamlit UI (main entry point)
├── requirements.txt
├── core/
│   ├── config.py             # Settings & environment config
│   └── database.py           # SQLite init & connection
├── models/
│   └── schemas.py            # Pydantic models (input/output)
├── ai/
│   └── email_generator.py    # OpenAI prompt engine (core AI module)
├── services/
│   ├── lead_service.py       # Lead import, CSV/JSON parsing, CRUD
│   └── campaign_service.py   # Campaign orchestration & stats
├── api/
│   └── main.py               # FastAPI REST endpoints
├── utils/
│   └── export.py             # CSV / JSON / TXT exporters
└── data/
    ├── sample_leads.csv       # 10 example leads
    ├── sample_output.json     # Example generated sequences
    └── outreach.db            # SQLite DB (auto-created)
```

---

## ⚙️ Setup & Run

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set OpenAI API Key

```bash
export OPENAI_API_KEY=sk-your-key-here
```

Or set it directly in the Streamlit sidebar at runtime.

### 3. Run the Streamlit UI

```bash
streamlit run app.py
```

Opens at: http://localhost:8501

### 4. Run the FastAPI Backend (optional, for API access)

```bash
uvicorn api.main:app --reload --port 8000
```

API docs at: http://localhost:8000/docs

---

## 🔄 System Flow

```
1. IMPORT LEADS
   CSV file OR JSON array OR manual entry
   → Creates Campaign + stores Leads in SQLite

2. GENERATE CAMPAIGN
   For each lead:
   → AI infers: pain_point, improvement_area, hook
   → AI writes: cold_email + followup_1 + followup_2
   → Stored in email_sequences table

3. VIEW & INSPECT
   Browse campaigns, preview email sequences per lead

4. EXPORT
   CSV  → CRM import, spreadsheet analysis
   JSON → API integration, developer use
   TXT  → Gmail / Outlook copy-paste
```

---

## 📧 Email Sequence Schedule

| Email       | Send Day | Purpose                          |
|-------------|----------|----------------------------------|
| Cold Email  | Day 1    | Personalized intro + soft CTA    |
| Follow-Up 1 | Day 3    | Insight or question              |
| Follow-Up 2 | Day 7    | Final nudge, leave door open     |

---

## 🔌 FastAPI Endpoints

| Method | Endpoint                          | Description                       |
|--------|-----------------------------------|-----------------------------------|
| POST   | /upload-leads                     | Upload CSV or JSON leads          |
| POST   | /campaigns                        | Create campaign with inline JSON  |
| POST   | /generate-campaign?campaign_id=…  | Trigger AI generation             |
| GET    | /campaigns                        | List all campaigns                |
| GET    | /campaign/{id}                    | Campaign details + stats          |
| GET    | /campaign/{id}/leads              | All leads in campaign             |
| GET    | /campaign/{id}/emails             | All generated emails              |
| GET    | /lead/{id}                        | Single lead details               |
| GET    | /lead/{id}/emails                 | Lead's email sequence             |
| GET    | /campaign/{id}/export/csv         | Download CSV                      |
| GET    | /campaign/{id}/export/json        | Download JSON                     |
| GET    | /campaign/{id}/export/text        | Download plain text               |

---

## 🤖 AI Module (`ai/email_generator.py`)

The AI module uses two sequential OpenAI calls per lead:

**Call 1 — Personalization Inference:**
- Extracts first name
- Infers industry-specific pain point
- Identifies improvement area (automation, lead gen, time saving, etc.)
- Generates a contextual hook line

**Call 2 — Email Sequence Generation:**
- Uses personalization data as context
- Generates 3 emails with strict length/tone guidelines
- Returns structured JSON (subject + body per email)

---

## 📦 Extending to SaaS

To productionize this MVP:

- **Auth:** Add JWT + user accounts (FastAPI + OAuth2)
- **Multi-tenancy:** Add `user_id` to all tables
- **Scheduler:** Integrate with SendGrid/Postmark for actual sending
- **Webhooks:** Track opens, clicks, replies
- **Queue:** Move generation to Celery + Redis for scale
- **Frontend:** Replace Streamlit with Next.js for branding

---

## 📄 CSV Format

```csv
name,email,company,industry,website,lead_score
Alice Johnson,alice@acme.com,Acme Corp,SaaS,https://acme.com,82
```

Required: `name`, `email`, `company`, `industry`
Optional: `website`, `lead_score` (0–100, default 50)


## Demo Video

[▶ Watch Demo](demo/demo.mp4)
