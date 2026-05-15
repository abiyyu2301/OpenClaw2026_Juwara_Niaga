# Niaga — Pitch Deck

Source content for the 5-slide PDF required for Devpost submission. Drop these into Google Slides / Keynote / PowerPoint and export as `OpenClaw2026_Juwara_Niaga.pdf`.

Per the Official Technical Guidelines: title page can mention team name and members briefly; **no separate introduction slide**.

---

## Slide 1 — Problem Statement

**Title:** Indonesian SMEs lose deals to manual sales.

**Body:**
- 65M+ Indonesian SMEs run sales like a chat thread: referrals, Instagram DMs, hand-typed quotes.
- Global AI sales tools (Clay, Apollo, Lavender) are built for US/EU markets — wrong language, wrong payment rails, wrong business etiquette.
- The cost: SMEs lose hot leads because the human sales loop is the bottleneck, not the deal economics.

**One number:** Indonesian SME software spend grows ~22%/year, but B2B sales tooling still trails consumer apps by a decade (Bain, 2025).

**Footer (small):** Team **Juwara** · Abiyyu Avicena · OpenClaw Agenthon 2026

---

## Slide 2 — Solution Overview

**Title:** Niaga is an autonomous AI sales team for Indonesian SMEs.

**Body:** Define your Ideal Customer Profile + offer once. Niaga then:

1. **Prospects** — researches each lead with structured profile output
2. **Debates** — Bull and Bear agents argue adversarially; Judge renders an explainable verdict
3. **Drafts & sends** — formal-but-warm Bahasa Indonesia outreach via Gmail SMTP
4. **Classifies replies** — by intent, sentiment, and recommended next action
5. **Closes commercially** — Closer agent decides the right DOKU payment event (deposit, pilot fee, workshop booking) and sends the link
6. **Onboards** — AfterCare agent fires a warm follow-up the moment payment succeeds

**The killer line:** *Zero human clicks from "new lead" to "paid deal".*

---

## Slide 3 — AI Agent Workflow & Technical Architecture

**Title:** Seven specialized agents + a deterministic orchestrator loop.

```
┌────────────────────────────────────────────────────────────┐
│           ORCHESTRATOR (deterministic, no LLM)              │
│  for each lead in unprocessed[:max_leads_per_run]:          │
│      profile  = Prospector.run(icp, lead, web_context)      │
│      bull, bear = parallel(Bull, Bear)                      │
│      verdict = Judge.decide(bull, bear, profile)            │
│      if qualified: email = Outreach.draft(profile, verdict) │
│                    send(email) -> await reply               │
│      if reply: intent = Reply.classify(reply)               │
│              if hot: link = Closer.decide_payment(intent)   │
│                      send(link) -> webhook                  │
│      on paid: AfterCare.followup(payment)                   │
└────────────────────────────────────────────────────────────┘
                  │
   Vertex AI Gemini 2.5 Flash + 2.5 Pro
                  │
   Gmail SMTP/IMAP  ·  DOKU Payment Link
```

Every agent decision is logged to the `agent_messages` table — the evidence locker that proves autonomy to the judges. The Live Agent Feed (WebSocket) streams every event to the browser in real time.

---

## Slide 4 — Key Features & Tech Stack

**Title:** Built for the Indonesian B2B market.

| Feature | Why it matters |
|---|---|
| **Adversarial Bull-vs-Bear debate** | Explainable qualification. The Judge's verdict cites both arguments — judges can SEE why a lead was qualified. |
| **Bahasa Indonesia native prose** | Gemini 2.5 Pro trained extensively on Indonesian. Outreach reads as warm formal BI, not translated English. |
| **DOKU as a commercial event** | Closer picks the right event type — deposit, pilot fee, workshop booking — not just "send a pay button". |
| **Live Agent Feed UI** | Watch the seven agents think. Per-agent colors, terminal-style streaming. The autonomy claim is *visible*. |
| **Autonomous + Supervised modes** | One env var to switch between fully autonomous and human-approval-between-steps for real-world deployability. |

**Stack:**
FastAPI · Python 3.12 · SQLAlchemy · plain async (no LangGraph overhead) · WebSocket · React + Vite + Tailwind · Vertex AI Gemini 2.5 (Flash for cheap, Pro for reasoning) · Gmail SMTP/IMAP · DOKU Payment Link API + MockPaymentProvider fallback · Sumopod VPS · SQLite (build) / Postgres-ready (deploy).

---

## Slide 5 — Future Development & Impact

**Title:** From one-language outreach to a multi-channel commercial agent.

**Roadmap:**
- **WhatsApp Business channel** — Indonesian SMEs live in WhatsApp. Add it as a parallel surface to email.
- **LinkedIn warming via Repliz** — programmatic engagement on prospect content before the first cold email.
- **Multi-language** — Javanese/Sundanese localization; Bahasa Melayu for cross-border (Singapore, Malaysia).
- **Broader payment rails** — QRIS, Virtual Account, e-wallets via DOKU's full Checkout API surface.
- **RAG over the merchant's CRM** — let Niaga reason against historical deal outcomes when qualifying new leads.

**Impact:** If Niaga gets 1% of Indonesia's 65M SMEs to automate a single deal flow, that's **650K SMEs reclaiming 10+ hours/week from manual sales** — a real productivity story for a market that doesn't get built for.

**Footer:** Demo video → (paste YouTube unlisted link) · GitHub → github.com/abiyyu2301/OpenClaw2026_Juwara_Niaga · Live → (paste Sumopod URL)
