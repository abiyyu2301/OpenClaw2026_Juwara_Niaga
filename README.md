# Niaga

**Autonomous multi-agent B2B sales platform for Indonesian SMEs.**

> Team **Juwara** · OpenClaw Agenthon 2026 · RISTEK Fasilkom UI × Build Club

Niaga is an autonomous AI sales team. Define an Ideal Customer Profile and an offer once, then watch seven specialized agents prospect leads, debate each one adversarially (Bull vs Bear vs Judge), draft personalized Bahasa Indonesia outreach, send email, classify replies, decide when to close, and send a DOKU payment link — all in one continuous loop with no human clicks in between.

## What makes it different

1. **Adversarial qualification** — Bull and Bear agents argue for and against each lead; a Judge agent renders an explainable verdict.
2. **End-to-end autonomy with payment as the closing event** — most "AI sales tools" stop at "email sent." Niaga goes all the way to receiving payment via DOKU.
3. **Indonesian SME wedge** — native Bahasa Indonesia outreach, local business etiquette, DOKU payment integration as a first-class commercial event.
4. **Live agent feed UI** — judges watch the agents think, debate, and act in real time.

## The seven agents

| # | Agent | Purpose |
|---|---|---|
| 1 | Prospector | Enrich raw lead with web data |
| 2 | Bull | Argue *for* pursuing the lead |
| 3 | Bear | Argue *against* the lead |
| 4 | Judge | Decide qualified/not (explainable) |
| 5 | Outreach | Draft + send Bahasa Indonesia email |
| 6 | Reply | Classify inbound reply intent |
| 7 | Closer | Decide and send DOKU payment link |

Plus an **Orchestrator** loop (deterministic, no LLM) and an **AfterCare** agent triggered by payment webhook.

## Tech stack

- **Backend**: FastAPI · Python 3.12 · SQLAlchemy · WebSocket
- **Frontend**: React · Vite · TypeScript · Tailwind CSS
- **LLM**: Google Gemini via Vertex AI (`gemini-2.5-pro` for reasoning, `gemini-2.5-flash` for fast/cheap tier)
- **Email**: Gmail SMTP (send) + IMAP (receive)
- **Payment**: DOKU Payment Link API · mock adapter fallback
- **Database**: SQLite (build) · Postgres-ready (deploy)
- **Hosting**: Sumopod VPS

## Getting started

### Prerequisites

- Python 3.12+
- Node.js 20+
- A GCP project with Vertex AI API enabled and a service account JSON key
- Gmail account with app password for SMTP/IMAP
- (Optional) DOKU sandbox credentials

### Setup

```bash
# 1. Clone and enter the repo
git clone https://github.com/<your-org>/OpenClaw2026_Juwara_Niaga.git
cd OpenClaw2026_Juwara_Niaga

# 2. Copy env template and fill in your secrets
cp .env.example .env
# Edit .env with your values (GCP_PROJECT_ID, GMAIL_*, etc.)

# 3. Place your service account JSON key at:
#    credentials/niaga-backend-key.json

# 4. Backend
cd backend
python -m venv venv
venv\Scripts\activate          # Windows PowerShell
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
python -m alembic upgrade head  # or: python -c "from db.session import Base, engine; Base.metadata.create_all(engine)"
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# 5. Frontend (in a new terminal)
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173> to view the dashboard. Backend API at <http://localhost:8000/docs>.

## Project structure

```
OpenClaw2026_Juwara_Niaga/
├── backend/              FastAPI · agents · orchestrator · DB · tools
│   ├── agents/           One file per agent + base + LLM client wrapper
│   ├── db/               SQLAlchemy models · session
│   ├── routes/           Campaign · lead · run · webhook endpoints
│   ├── tools/            Web search · email · payment provider
│   └── tests/            Pipeline smoke tests
├── frontend/             React + Vite + Tailwind
│   └── src/
│       ├── pages/        Dashboard · CampaignNew · CampaignRun · Leads · LeadDetail
│       └── components/   AgentFeed · DebatePanel · LeadKanban · PaymentTimeline
├── credentials/          (gitignored) Service account JSON key
├── data/                 Demo leads CSV
└── docs/                 Build plan + architecture
```

## Demo

A demo video is available at the YouTube link in our Devpost submission. Live deployment: see Devpost link.

## License

MIT
