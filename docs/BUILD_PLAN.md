# Niaga — Build Plan & Architecture

**Project**: Autonomous multi-agent B2B sales platform for Indonesian SMEs
**Competition**: RISTEK x Build Club OpenClaw Agenthon 2026
**Build window**: 12 hours (15 May 2026, 09:45 → 23:00 WIB)
**Submission deadline**: 15 May 2026, 23:00 WIB via Devpost

---

## 0. Context for Claude Code

You are picking up an agentic AI project for a 12-hour hackathon. This document is the single source of truth. Before writing any code, read sections 1–6 in full. Sections 7–11 are the hour-by-hour build instructions.

**Hard rules from the competition**:
- The agent must run **autonomously** without human intervention to complete at least 1 task end-to-end
- The system must have a **tool-calling capability** (real external API calls, not just LLM responses)
- The system must have an **autonomous loop** (the agent decides what to do next, not a human)
- **Pure chatbot wrappers are penalized**. The agent must reason, call tools, make decisions, and act on them
- GitHub repo must be created **after 09:45 WIB on 15 May 2026** with commit history spread across the build window
- Repo naming: `OpenClaw2026_<TeamName>_Niaga`

**Judging weights** (design every decision against these):
| Criterion | Weight |
|---|---|
| Use Case Clarity & Impact | 10% |
| Creativity & Originality | 30% |
| Autonomy & Agent Behaviour | 30% |
| Technical Execution | 20% |
| Real-World Deployability | 10% |
| **Bonus**: Best Payment Use Case (DOKU) | separate award |

---

## 1. Concept (One Paragraph)

Niaga is an autonomous multi-agent sales team for Indonesian SMEs. A user defines an Ideal Customer Profile and an offer once; from that point on, the system prospects target companies via web search, **debates each lead adversarially** (Bull agent vs Bear agent, decided by a Judge agent), drafts personalized **Bahasa Indonesia** outreach, sends email, classifies replies, decides when to close, and sends a **DOKU payment link** for a deposit, pilot fee, or training booking — all in one continuous orchestrator loop. The human watches a live agent feed, can pause the run, but never has to click "approve" between steps.

---

## 2. What Makes This Win (Differentiation)

This is *not* "AI for lead gen" — that space is saturated (Clay, Apollo, Lavender). The wedges are:

1. **Adversarial multi-agent qualification** — Bull vs Bear vs Judge produces *explainable* fit scores. Nobody else does this; it demos beautifully.
2. **End-to-end autonomy with payment as the closing event** — most "AI sales tools" stop at "email sent." Niaga goes all the way to receiving payment.
3. **Indonesian SME wedge** — Bahasa Indonesia outreach, local business etiquette, DOKU payment integration as native, not bolted on.
4. **Live agent feed UI** — judges literally watch the agents think. This is the visual that makes the autonomy claim believable.

---

## 3. System Architecture

```
                    ┌────────────────────────────────────┐
                    │           Frontend (React)          │
                    │  Campaign setup · Agent live feed   │
                    │  Lead board · Debate viewer         │
                    │  Inbox · Payment timeline           │
                    └─────────────────┬──────────────────┘
                                      │ REST + WebSocket
                                      ▼
                    ┌────────────────────────────────────┐
                    │     FastAPI Backend (Sumopod VPS)   │
                    │  Auth · CRUD · Run controller       │
                    │  Webhook receivers · Event stream   │
                    └─────────────────┬──────────────────┘
                                      │
                                      ▼
        ┌─────────────────────────────────────────────────────────┐
        │              ORCHESTRATOR AGENT (the loop)               │
        │  while (campaign.active && budget_remaining):            │
        │      lead = next_unprocessed()                           │
        │      profile = ProspectorAgent.enrich(lead)              │
        │      bull, bear = parallel(BullAgent, BearAgent)         │
        │      verdict = JudgeAgent.decide(bull, bear, profile)    │
        │      if verdict.qualified:                                │
        │          msg = OutreachAgent.draft(profile, verdict)     │
        │          send(msg) → wait_or_continue()                  │
        │      if reply_received:                                   │
        │          intent = ReplyAgent.classify(reply)             │
        │          action = NegotiatorAgent.decide(intent)         │
        │          if action == "close":                            │
        │              CloserAgent.send_doku_link(amount, lead)    │
        │      on payment_webhook: AfterCareAgent.followup()       │
        └─────────────────────────────────────────────────────────┘
                                      │
                ┌─────────────────────┼─────────────────────┐
                ▼                     ▼                     ▼
      ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
      │   AGENT TOOLS     │  │   POSTGRES DB     │  │  INTEGRATIONS    │
      │  web_search       │  │  campaigns        │  │  Gmail SMTP/IMAP  │
      │  fetch_page       │  │  leads            │  │  DOKU Payment Link│
      │  search_company   │  │  agent_runs       │  │  DOKU webhook     │
      │  draft_email      │  │  agent_messages   │  │  Sumopod LLM API  │
      │  send_email       │  │  debates          │  └──────────────────┘
      │  check_inbox      │  │  outreach_drafts  │
      │  create_doku_link │  │  replies          │
      │  log_decision     │  │  payment_events   │
      └──────────────────┘  └──────────────────┘
```

### 3.1 The Seven Agents

| # | Agent | Purpose | Input | Output |
|---|---|---|---|---|
| 1 | **Prospector** | Enrich raw lead with web data | Company name, website, role | Structured profile JSON |
| 2 | **Bull** | Argue *for* pursuing the lead | Profile + ICP | 3 reasons + est. deal value |
| 3 | **Bear** | Argue *against* the lead | Profile + ICP | 3 objections + est. waste risk |
| 4 | **Judge** | Decide qualified/not | Bull + Bear args + profile | `{qualified, fit_score, confidence, reasoning, angle}` |
| 5 | **Outreach** | Draft + send Bahasa Indonesia email | Profile + angle + offer | Email subject + body |
| 6 | **Reply** | Classify inbound reply | Email text | `{intent, sentiment, next_action}` |
| 7 | **Closer** | Decide and send DOKU link | Intent + lead state | Payment link sent |
| — | **Orchestrator** | The loop. No LLM. | Campaign state | Drives all agents |
| — | **AfterCare** | Triggered by payment webhook | Payment event | Onboarding email |

### 3.2 Autonomy Modes

- **Autonomous mode** (DEFAULT — demo with this on): The orchestrator runs end-to-end. Outreach agent sends emails without approval. Closer sends DOKU links without approval. Only stops on `pause_run` or end of campaign.
- **Supervised mode** (toggle): Same flow, but pauses for human approval at `send_email` and `create_payment_link` steps. Use this in the pitch deck's "Real-World Deployability" slide to show maturity.

---

## 4. Model Strategy

The agents use Sumopod's OpenAI-compatible AI gateway (`ai.sumopod.com`). **Make every agent's model configurable via env var.** At session start, check the Sumopod dashboard for the exact model IDs they offer and update `.env` accordingly.

### 4.1 Recommended Tiering

| Agent | Tier | Preferred (in order) | Fallback |
|---|---|---|---|
| Prospector | Mid | Claude Sonnet 4.6 → GPT-5 mini → Gemini 2.5 Flash | DeepSeek V3 |
| Bull | Cheap | Haiku 4.5 → Gemini Flash → DeepSeek V3 | Any cheap model |
| Bear | Cheap | Same as Bull | Same |
| Judge | **Premium** | Claude Sonnet 4.6 → GPT-5.4 → Gemini 3.1 Pro | Sonnet |
| Outreach | **Premium** | Claude Sonnet 4.6 → GPT-5.4 | Sonnet (best BI prose) |
| Reply | Mid | Haiku 4.5 → Gemini Flash → GPT-5 mini | Cheap tier |
| Closer | Mid | Claude Sonnet 4.6 → Gemini 2.5 Flash | Mid tier |

Rationale: Bull and Bear are designed to disagree at low cost (they're rhetorical sparring partners, not deciders). Judge and Outreach are where quality matters most — Judge produces the explainable verdict, Outreach produces the natural Bahasa Indonesia prose that judges will read in demo emails.

### 4.2 Cost Controls (Bake Into Code)

- Max 10 leads per autonomous run (configurable via campaign settings)
- Output token caps: Bull/Bear 800, Outreach 1500, Reply 600, Judge 1200, Closer 1000
- Stream responses where the UI needs them; otherwise non-streaming
- Log `prompt_tokens`, `completion_tokens`, `model`, `cost_estimate` to `agent_messages` per call
- Implement a 5-minute hard wall-clock timeout on any single agent call

### 4.3 LLM Client Wrapper

Create one shared client (`backend/agents/llm.py`) that all agents use. Single Sumopod OpenAI-compatible client; agents pass their preferred model name. Wrapper handles: timeout, retries on rate limit, token logging, JSON-mode fallback (some models don't support strict JSON — use response prefilling instead).

---

## 5. Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| IDE | **Cursor** | Use credits aggressively to scaffold |
| Backend | **FastAPI + Python 3.11** | Best agent ecosystem, async-native |
| Agent framework | Plain async Python (no LangGraph) | Smaller surface area; in 12 hours, framework debugging kills you |
| LLM gateway | **Sumopod** at `https://ai.sumopod.com/v1` | OpenAI-compatible; use the `openai` Python SDK |
| Database | **SQLite** for build, **Postgres** if time permits | SQLite ships fine for demo; Postgres looks more professional if deployed |
| Frontend | **React + Vite + Tailwind** | Fast cold start, no SSR overhead |
| Realtime | **FastAPI WebSocket** | Stream agent events to the live feed |
| Email | **Gmail SMTP** (send) + **IMAP polling** (receive) with app password | Real email in demo; no third-party email service to set up |
| Payment | **DOKU Payment Link API** + mock adapter fallback | Two implementations behind one interface |
| Hosting | **Sumopod VPS** | Use the 100k credits for the VPS; deploy live URL for Real-World Deployability |
| Web search tool | **DuckDuckGo HTML scrape** or **Serper.dev free tier** | No paid Google API needed |

### 5.1 Tools That Stay Out of MVP

- **Repliz** — social media comment automation, doesn't fit B2B email lead-gen. Mention in pitch deck as "future expansion: LinkedIn warming via Repliz."
- **LangGraph/CrewAI** — overhead too high for 12 hours; plain async functions work
- **LinkedIn scraping** — TOS violation, do not build
- **Vector database / RAG** — only add in last 2 hours if there's time AND it strengthens the demo

---

## 6. Database Schema

Nine tables. Use SQLAlchemy ORM. Migrations via Alembic only if Postgres; for SQLite, just `Base.metadata.create_all()`.

```sql
-- Define ICP + offer once per campaign
campaigns(
  id, name, target_industry, company_size, geography,
  buyer_role, pain_points, offer, pricing_range_min, pricing_range_max,
  currency, disqualifiers, autonomous_mode BOOL DEFAULT true,
  max_leads_per_run INT DEFAULT 10, created_at
)

-- Raw lead records (CSV uploaded or prospected)
leads(
  id, campaign_id, company_name, industry, website, linkedin_url,
  buyer_name, buyer_role, email, raw_notes, status, created_at
)
-- status values: new, profiling, profiled, debating, qualified, disqualified,
--                outreach_sent, replied, warm, closing, payment_pending,
--                paid, lost, do_not_contact

-- Prospector output
lead_ai_profiles(
  id, lead_id, why_relevant, detected_trigger, fit_score,
  confidence_level, source_evidence_json, recommended_outreach_angle,
  tokens_used, created_at
)

-- The Bull/Bear/Judge debate (this is your demo differentiator — store it well)
debates(
  id, lead_id, bull_argument_json, bear_argument_json,
  verdict, fit_score, confidence, reasoning,
  recommended_angle, tokens_used, created_at
)

-- Drafted and sent outreach
outreach_drafts(
  id, lead_id, draft_type, language, subject, body,
  sent_at, smtp_message_id, status, created_at
)
-- draft_type: first_email, follow_up_1, follow_up_2, objection_reply, meeting_request
-- status: drafted, approved, sent, failed

-- Inbound classified replies
replies(
  id, lead_id, raw_reply_text, classification, sentiment,
  confidence, recommended_next_action, suggested_response,
  new_lead_status, received_at, created_at
)
-- classification values: interested, not_now, not_relevant, wrong_person,
--   request_for_info, pricing_question, meeting_requested,
--   unsubscribe_do_not_contact, negative_response

-- DOKU payment events
payment_events(
  id, lead_id, commercial_event_type, amount, currency,
  payment_link, payment_status, doku_reference_id,
  expires_at, paid_at, created_at, updated_at
)
-- commercial_event_type: paid_trial, pilot_fee, consultation_deposit,
--   onboarding_fee, subscription_first, workshop_booking, renewal
-- payment_status: created, pending, paid, failed, expired, refunded

-- One row per orchestrator run session
agent_runs(
  id, campaign_id, started_at, ended_at, leads_processed,
  leads_qualified, emails_sent, deals_closed, total_revenue,
  total_tokens, status, error_message
)
-- status: running, completed, paused, failed

-- THE EVIDENCE LOCKER for "Autonomy & Agent Behaviour" judging
-- One row per agent action, including reasoning and tool calls
agent_messages(
  id, run_id, lead_id, agent_name, role,
  content TEXT, tool_calls_json, tool_results_json,
  prompt_tokens, completion_tokens, model, latency_ms, created_at
)
-- role: thought, tool_call, tool_result, decision, message_out
```

`agent_messages` is non-negotiable. Every LLM call and every tool call writes a row. The Live Agent Feed reads from this table over WebSocket. When a judge asks "how do you know it's autonomous," you open this table.

---

## 7. Agent Prompts

Each agent has its own prompt file at `backend/agents/prompts/<agent>.txt`. **Use JSON-mode output for every agent.** Provide a JSON schema in the system prompt and parse strictly. Fall back to JSON repair if the model returns malformed output.

### 7.1 Prospector Agent

```
You are a B2B sales analyst researching Indonesian SMEs for a sales campaign.

CAMPAIGN ICP:
{icp_json}

LEAD DATA:
{lead_json}

WEB CONTEXT (from search tools):
{web_context}

Produce a structured profile. Be honest about evidence weakness.
If you cannot find strong evidence, lower the confidence and say so.
Never invent facts not present in the web context.

Return JSON with exactly these keys:
{
  "company_name": string,
  "industry": string,
  "likely_buyer": string,
  "why_relevant": string (2-3 sentences),
  "detected_trigger": string (a recent signal or pain),
  "estimated_fit_score": int 0-100,
  "confidence_level": "Low" | "Medium" | "High",
  "source_evidence": [string array, max 5 items],
  "recommended_outreach_angle": string (1-2 sentences)
}
```

### 7.2 Bull Agent

```
You are an aggressive sales development representative.
Your job: argue strongly that this lead is WORTH pursuing.
Even if the lead is mediocre, find the strongest case.

LEAD PROFILE:
{profile_json}

CAMPAIGN OFFER:
{offer_json}

Return JSON:
{
  "top_reasons": [3 strings, each a single compelling argument],
  "estimated_deal_value_idr": int,
  "estimated_close_probability": float 0.0-1.0,
  "urgency": "low" | "medium" | "high"
}

Be specific. Reference details from the profile. No generic statements.
```

### 7.3 Bear Agent

```
You are a skeptical sales operations manager.
Your job: argue strongly that pursuing this lead is a WASTE of time.
Even if the lead looks great, find the strongest objections.

LEAD PROFILE:
{profile_json}

CAMPAIGN OFFER:
{offer_json}

Return JSON:
{
  "top_objections": [3 strings, each a concrete risk],
  "estimated_time_waste_hours": int,
  "estimated_disqualifier_probability": float 0.0-1.0,
  "red_flags": [string array]
}

Be specific. Reference details from the profile. No generic objections.
```

### 7.4 Judge Agent

```
You are the head of sales. Two of your SDRs have argued about whether
to pursue this lead. Read both arguments and decide.

PROFILE: {profile_json}
BULL ARGUMENT: {bull_json}
BEAR ARGUMENT: {bear_json}
ICP: {icp_json}

Be decisive. Explain your reasoning so a junior salesperson can learn.

Return JSON:
{
  "qualified": boolean,
  "fit_score": int 0-100,
  "confidence": "Low" | "Medium" | "High",
  "reasoning": string (3-4 sentences explaining the decision),
  "key_factor": string (the single most decisive point),
  "recommended_outreach_angle": string,
  "estimated_pilot_amount_idr": int (relevant payment amount if closed)
}
```

### 7.5 Outreach Agent

```
You are a senior B2B sales rep writing in Bahasa Indonesia to Indonesian SME owners.

LEAD PROFILE: {profile_json}
JUDGE'S ANGLE: {angle}
OFFER: {offer_json}

Write a first-touch cold email in formal-but-warm Bahasa Indonesia.
Indonesian business culture: respectful, builds relationship before pitch.
NO aggressive sales language. NO "ROI calculators" or jargon.
Reference 1 specific detail from the profile (proves you researched).
Keep email under 150 words. Sign as "Tim Niaga".

Return JSON:
{
  "subject": string (Bahasa Indonesia, under 60 chars),
  "body": string (Bahasa Indonesia, plain text, paragraphs separated by \n\n),
  "call_to_action": string (one sentence — what response do you want?)
}
```

### 7.6 Reply Agent

```
You are a CRM reply classifier.

LEAD: {lead_summary}
OUR LAST EMAIL: {last_outreach_summary}
THEIR REPLY: {reply_text}

Classify the reply intent. If they ask multiple things, pick the dominant intent.

Return JSON:
{
  "classification": one of [
    "interested", "not_now", "not_relevant", "wrong_person",
    "request_for_info", "pricing_question", "meeting_requested",
    "unsubscribe_do_not_contact", "negative_response"
  ],
  "confidence": "Low" | "Medium" | "High",
  "sentiment": "positive" | "neutral" | "negative",
  "extracted_questions": [string array of specific questions they asked],
  "recommended_next_action": one of [
    "send_pricing", "schedule_meeting", "send_payment_link",
    "send_followup", "stop_contact", "escalate_to_human"
  ],
  "new_lead_status": string (one of the lead.status values),
  "reasoning": string (1-2 sentences)
}
```

### 7.7 Closer Agent

```
You are a sales closer. A lead has reached commercial intent.
Decide whether to send a DOKU payment link, and which type.

LEAD: {lead_summary}
REPLY ANALYSIS: {reply_analysis}
ICP PRICING RANGE: {pricing_range_idr}

DOKU commercial event types available:
- paid_trial: small commitment fee, 100-500k IDR
- pilot_fee: 1-month pilot project, 1-5M IDR
- consultation_deposit: refundable, 250-500k IDR
- workshop_booking: training session deposit, 500k-2M IDR
- subscription_first: first month full price

Return JSON:
{
  "should_send_payment_link": boolean,
  "commercial_event_type": one of the above OR null,
  "amount_idr": int OR null,
  "rationale": string,
  "follow_up_message_bahasa": string (the email to send WITH the link),
  "expires_in_hours": int (default 72)
}

If should_send_payment_link is false, explain in rationale and set other fields to null.
```

### 7.8 AfterCare Agent

```
You are a customer success specialist. A payment event just occurred.

LEAD: {lead_summary}
PAYMENT EVENT: {event_json}
PAYMENT STATUS: {status}

Statuses: created, pending, paid, failed, expired, refunded

Write a Bahasa Indonesia follow-up email appropriate to the status.
Never pressure the customer. For "paid", be warm and outline next steps.
For "expired", offer to issue a fresh link.

Return JSON:
{
  "should_send": boolean,
  "subject": string,
  "body": string (Bahasa Indonesia, under 100 words),
  "internal_note": string (note for the sales team CRM)
}
```

---

## 8. The Orchestrator Loop

`backend/orchestrator.py`. This is the **autonomous loop** the competition rules mandate. Pseudocode:

```python
async def run_campaign(campaign_id: int, run_id: int):
    campaign = await db.get_campaign(campaign_id)
    leads = await db.get_unprocessed_leads(campaign_id, limit=campaign.max_leads_per_run)

    for lead in leads:
        if await is_paused(run_id):
            break

        # 1. Prospect (enrich with web search)
        await update_lead_status(lead.id, "profiling")
        await stream_event(run_id, "Prospector", f"Researching {lead.company_name}...")
        profile = await ProspectorAgent.run(lead, campaign)
        await db.save_profile(profile)

        # 2. Adversarial debate (parallel for speed)
        await update_lead_status(lead.id, "debating")
        await stream_event(run_id, "Bull", "Building case FOR...")
        await stream_event(run_id, "Bear", "Building case AGAINST...")
        bull, bear = await asyncio.gather(
            BullAgent.run(profile, campaign),
            BearAgent.run(profile, campaign)
        )
        await stream_event(run_id, "Judge", "Reviewing arguments...")
        verdict = await JudgeAgent.run(profile, bull, bear, campaign)
        await db.save_debate(lead.id, bull, bear, verdict)

        if not verdict.qualified:
            await update_lead_status(lead.id, "disqualified")
            await stream_event(run_id, "Judge",
                f"Disqualified: {verdict.key_factor}")
            continue

        # 3. Outreach
        await update_lead_status(lead.id, "qualified")
        await stream_event(run_id, "Outreach", "Drafting Bahasa Indonesia email...")
        email = await OutreachAgent.run(profile, verdict, campaign)

        if campaign.autonomous_mode:
            await stream_event(run_id, "Outreach",
                f"Sending to {lead.email}...")
            message_id = await send_email_smtp(lead.email, email.subject, email.body)
            await db.save_outreach(lead.id, email, sent=True, message_id=message_id)
            await update_lead_status(lead.id, "outreach_sent")
        else:
            # Supervised mode: save as drafted, await approval
            await db.save_outreach(lead.id, email, sent=False)

    # Inbox polling loop continues separately (see 8.1)

async def inbox_loop(run_id: int):
    """Runs as background task while orchestrator processes leads."""
    while await is_run_active(run_id):
        new_replies = await poll_imap_inbox()
        for reply in new_replies:
            lead = await match_reply_to_lead(reply)
            if not lead:
                continue
            await stream_event(run_id, "Reply", f"Classifying reply from {lead.company_name}...")
            classification = await ReplyAgent.run(reply, lead)
            await db.save_reply(lead.id, reply, classification)
            await update_lead_status(lead.id, classification.new_lead_status)

            if classification.recommended_next_action == "send_payment_link":
                await stream_event(run_id, "Closer", "Lead is hot. Deciding payment link...")
                decision = await CloserAgent.run(lead, classification, campaign)
                if decision.should_send_payment_link and campaign.autonomous_mode:
                    payment_link = await PaymentProvider.create(
                        amount=decision.amount_idr,
                        event_type=decision.commercial_event_type,
                        lead_id=lead.id,
                        expires_in_hours=decision.expires_in_hours
                    )
                    await send_email_smtp(
                        lead.email,
                        f"[Pembayaran] {decision.commercial_event_type}",
                        decision.follow_up_message_bahasa + f"\n\nLink: {payment_link.url}"
                    )
                    await update_lead_status(lead.id, "payment_pending")
        await asyncio.sleep(15)

async def on_payment_webhook(event: DOKUWebhookEvent):
    """Triggered by DOKU webhook (or mock button)."""
    payment = await db.get_payment_by_doku_ref(event.reference_id)
    await db.update_payment_status(payment.id, event.status)
    lead = await db.get_lead(payment.lead_id)
    aftercare = await AfterCareAgent.run(lead, payment, event.status)
    if aftercare.should_send:
        await send_email_smtp(lead.email, aftercare.subject, aftercare.body)
    if event.status == "paid":
        await update_lead_status(lead.id, "paid")
```

### 8.1 Streaming Events to the Frontend

Every `stream_event(run_id, agent_name, content)` call:
1. Writes to `agent_messages` table
2. Broadcasts to WebSocket subscribers of `/ws/runs/{run_id}`
3. Frontend renders in the Live Agent Feed component

The feed is your single most important demo asset.

---

## 9. DOKU Integration

DOKU is the **commercial event layer**, not a "pay button." Build a `PaymentProvider` interface with two implementations.

### 9.1 Interface

```python
class PaymentProvider(ABC):
    @abstractmethod
    async def create_payment_link(
        self, amount: int, currency: str,
        description: str, expires_in_hours: int,
        lead_id: int, reference: str
    ) -> PaymentLink: ...

    @abstractmethod
    async def get_status(self, reference_id: str) -> str: ...

    @abstractmethod
    async def verify_webhook(self, headers: dict, body: bytes) -> bool: ...
```

### 9.2 Mock Implementation (always-works fallback)

Returns `https://niaga.local/mock-pay/{uuid}`. UI exposes simulated status buttons (mark paid, mark expired, mark failed) that POST to the webhook handler internally. This lets you demo the full workflow even without DOKU credentials.

### 9.3 Real Implementation

In Phase 0, register for a DOKU sandbox account. If credentials arrive in time, swap to real implementation behind the same interface (no other code changes). DOKU Payment Link API docs: `docs.doku.com`. The webhook handler verifies signature, parses the event, calls `on_payment_webhook`.

### 9.4 Demo Strategy for Payment

Pick **one** payment scenario and polish it. Recommended:

> Lead asks for pricing → Closer Agent decides to send Rp500.000 workshop booking deposit → DOKU link generated → User clicks (or mock button) → Webhook fires → AfterCareAgent sends Bahasa Indonesia onboarding email confirming the booking.

This is your Payment Track winning shot. Don't dilute it by demoing 5 different payment types.

---

## 10. Frontend (React + Vite + Tailwind)

Routes:
- `/` — dashboard (total leads, qualified, sent, replied, paid, revenue)
- `/campaigns/new` — ICP + offer setup form
- `/campaigns/:id` — campaign detail
- `/campaigns/:id/run` — **the live demo screen** (see below)
- `/leads` — kanban board of all leads with status badges
- `/leads/:id` — drill-down: profile, debate, outreach history, replies, payment

### 10.1 The Live Agent Feed (Demo Centerpiece)

A single page split into 3 columns:

| Left (40%) | Center (35%) | Right (25%) |
|---|---|---|
| **Lead Pipeline** | **Agent Feed** | **Active Lead Detail** |
| Kanban of leads, status badges update live | Monospace, terminal-like, color-coded per agent. Streams every event from WebSocket. Auto-scroll. | Currently-processing lead: company name, profile snippet, Bull vs Bear debate side-by-side, Judge verdict card |

Top bar: `▶ Start Autonomous Run` / `⏸ Pause` / `■ Stop`. Run counter, token usage, deals closed, revenue collected.

Use a distinctive but professional aesthetic — refer to the frontend-design skill. Avoid generic dashboard look. Niaga is Indonesian; consider warm earth tones (terracotta, sandstone) over the typical purple/blue SaaS palette. Distinctive headers, monospace for the agent feed contrasted with serif for the lead profiles.

---

## 11. Twelve-Hour Build Plan

Adjust start time to match actual competition start. Below assumes start at 09:45 WIB.

### Phase 0 — Lock & Load (09:45 → 10:15, 30 min)

In parallel across team:
- Person A: Create GitHub repo `OpenClaw2026_<TeamName>_Niaga`, push empty README, init backend + frontend skeleton with Cursor
- Person B: Register Devpost team, submit team naming
- Person C: Provision Sumopod VPS, confirm SSH access, deploy "hello world"
- Person D: Sumopod AI dashboard — note exact model IDs available; sign up for DOKU sandbox; create Gmail account or app password for agent's outbound email

**Lock the demo scenario**: ICP = Indonesian corporate training providers in Jakarta (10–100 employees), offer = Niaga pilot at Rp3M, payment demo = Rp500k workshop booking deposit.

### Phase 1 — Skeleton (10:15 → 11:45, 90 min)

- FastAPI app with health check
- 9 SQLAlchemy models matching section 6 schema; SQLite for now
- React app with placeholder routes
- WebSocket endpoint at `/ws/runs/{run_id}` (echo for now)
- `.env` with Sumopod base URL + API key
- LLM client wrapper at `backend/agents/llm.py` using `openai` SDK pointed at Sumopod
- **Deploy this empty app to Sumopod VPS already** — don't wait

Smoke test by 11:45: open the React app on the deployed URL, hit a backend health endpoint.

### Phase 2 — Core Reasoning Agents (11:45 → 14:30, 165 min)

- Implement `BaseAgent` class with: prompt loading, LLM call via wrapper, JSON parsing with repair fallback, `agent_messages` logging, token accounting
- Implement Prospector → save profile to DB
- Implement Bull, Bear → parallel via `asyncio.gather`
- Implement Judge → save debate to DB
- Build a quick CLI test: `python test_pipeline.py --lead "PT Mitra Edukasi"` runs Prospector→Bull→Bear→Judge end-to-end and prints all messages

Stretch in this phase: build the Live Agent Feed WebSocket stream and minimal UI. Don't leave it for the end.

Smoke test by 14:30: run 1 lead through Prospector→Bull→Bear→Judge, see all 4 agents' outputs in DB and in the agent feed.

### Phase 3 — Outreach + Email Loop (14:30 → 16:30, 120 min)

- Outreach Agent with Bahasa Indonesia prompt
- Gmail SMTP send via `aiosmtplib`
- IMAP poller via `aioimaplib` polling every 15s, matches by Message-ID / In-Reply-To headers
- Reply Agent with classification prompt
- Orchestrator: wire Prospector → Debate → Outreach → Send → Poll for reply → Classify
- Test with a real email round-trip to your own inbox

Smoke test by 16:30: run sends a real email; you reply from your phone; system classifies the reply and updates lead status.

### Phase 4 — DOKU Closer (16:30 → 18:30, 120 min)

- `PaymentProvider` abstract + `MockPaymentProvider` first
- Closer Agent prompt
- Webhook endpoint at `POST /webhooks/doku` with signature verification placeholder
- AfterCare Agent prompt
- UI: payment timeline component on lead detail page with status badges and (in mock mode) simulated status buttons
- If DOKU sandbox credentials arrived, implement `DOKUPaymentProvider`; otherwise stick with mock and label clearly in the demo as "DOKU sandbox-ready adapter"

Smoke test by 18:30: end-to-end run on 1 lead — prospects, debates, qualifies, sends email, classifies reply, decides to close, creates payment link, simulates payment, AfterCareAgent sends onboarding email.

### Phase 5 — Demo UX Polish (18:30 → 20:00, 90 min)

- Refine the Live Agent Feed: color per agent (Prospector teal, Bull green, Bear red, Judge gold, Outreach blue, Reply purple, Closer terracotta), timestamps, smooth auto-scroll, "tool_call" rows visually distinct
- Bull vs Bear side-by-side panel with Judge verdict card below
- Lead kanban with live status updates via WebSocket
- Dashboard tiles: total processed, qualified, emails sent, replies received, deals closed, revenue collected — all populated from real demo run
- Pause / Resume / Stop buttons functional

### Phase 6 — Demo Prep & Final Deploy (20:00 → 21:30, 90 min)

- Final deploy to Sumopod VPS
- Seed demo dataset: 3 leads
  - **Strong fit** (Bull wins decisively, Judge qualifies, will close)
  - **Weak fit** (Bear wins, Judge disqualifies — shows the system says NO sometimes)
  - **Genuinely ambiguous** (Bull and Bear actually disagree — Judge has to reason — best demo moment)
- Pre-stage reply texts you can inject if real email is slow during recording
- Record full screen capture of an autonomous run as backup video
- Verify all commit history shows distributed work across the 12 hours
- README with: project description, architecture diagram (ASCII from section 3), setup instructions, `.env.example`, demo dataset path, video link, live URL

### Phase 7 — Pitch & Submit (21:30 → 23:00, 90 min)

**Pitch Deck (PDF, exactly 5 slides)**:
1. **Problem** — Indonesian SMEs lose deals to manual sales. Global tools aren't built for our market.
2. **Solution** — Niaga: autonomous multi-agent B2B sales team with adversarial qualification, BI outreach, DOKU close.
3. **AI Agent Workflow / Architecture** — the diagram from section 3
4. **Key Features & Tech Stack** — 7 agents, autonomous loop, live agent feed, DOKU as commercial event, Sumopod-hosted, Bahasa Indonesia native
5. **Future Development / Impact** — LinkedIn warming, WhatsApp channel, multi-language, broader Indonesian payment rails

Naming: `OpenClaw2026_<TeamName>_Niaga.pdf`

**Demo Video (≤2 min, YouTube unlisted)**:
Script:

| Time | Scene | Talking point |
|---|---|---|
| 0:00–0:15 | Problem | "Indonesian SMEs lose deals because sales is manual. Global tools aren't built for our market." |
| 0:15–0:30 | Setup | Show campaign form: ICP = training providers, offer = pilot at Rp3M. Click **Start Autonomous Run**. |
| 0:30–1:00 | **Live Agent Feed** | "Watch the agents work." Show Prospector calling web_search, Bull vs Bear debating on screen, Judge rendering verdict. Disqualifies 1 lead — show it. |
| 1:00–1:20 | Outreach + reply | Bahasa Indonesia email sent autonomously. Lead replies asking pricing. Reply Agent classifies live. |
| 1:20–1:45 | **DOKU close** | Closer Agent decides to send Rp500k workshop deposit link. DOKU page shown. Mark as paid. AfterCareAgent fires onboarding email automatically. |
| 1:45–2:00 | Wrap | Dashboard shows: 3 leads processed → 1 disqualified → 1 deal closed → Rp500.000 collected. "Fully autonomous. No human clicks. Built in 12 hours." |

Naming: `OpenClaw2026_<TeamName>_Niaga.mp4` (then upload to YouTube unlisted).

**Devpost Submission Checklist**:
- [ ] Project Description (narrative)
- [ ] GitHub repo (public, README, instructions reproducible)
- [ ] Demo Video YouTube unlisted link
- [ ] Pitch Deck PDF uploaded
- [ ] Live Deployment Link (Sumopod URL)
- [ ] AI Tools / Models Used (Sumopod + the specific models per agent)
- [ ] **Label: "Best Payment Use Case"** ← do not forget

---

## 12. Risk Register & Mitigations

| Risk | Mitigation |
|---|---|
| Sumopod model unavailable / rate limited | Env-var-configurable per agent; have 2 fallback model IDs per agent |
| Real email delivery delay during recording | Pre-staged reply texts that can be injected manually; backup screen recording from earlier successful run |
| DOKU sandbox credentials never arrive | Mock provider is first-class, labelled as "sandbox-ready adapter" in demo |
| Sumopod VPS deploy issues at hour 11 | Deployed empty app at hour 1; redeploy continuously throughout |
| Multi-agent costs blow 100k credits | Cap to 10 leads/run; cheap models for Bull/Bear; output token caps; cost logged per agent |
| GitHub commit history looks compressed | Commit every 20–30 min; no giant end-of-day pushes |
| Pure-chatbot scoring penalty | Live Agent Feed proves autonomy; agent_messages table is the evidence; orchestrator loop is named and visible in pitch deck |
| Frontend not done in time | Backend-first; frontend can be ugly but functional. Live Agent Feed is the only screen that MUST look good. |

---

## 13. File Tree (Target State at End of Phase 1)

```
OpenClaw2026_<TeamName>_Niaga/
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml          # for local dev
├── backend/
│   ├── pyproject.toml
│   ├── app.py                  # FastAPI entrypoint
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy models (9 tables)
│   │   └── session.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py             # BaseAgent class
│   │   ├── llm.py              # Sumopod client wrapper
│   │   ├── prospector.py
│   │   ├── bull.py
│   │   ├── bear.py
│   │   ├── judge.py
│   │   ├── outreach.py
│   │   ├── reply.py
│   │   ├── closer.py
│   │   ├── aftercare.py
│   │   └── prompts/
│   │       ├── prospector.txt
│   │       ├── bull.txt
│   │       ├── bear.txt
│   │       ├── judge.txt
│   │       ├── outreach.txt
│   │       ├── reply.txt
│   │       ├── closer.txt
│   │       └── aftercare.txt
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── web_search.py       # DuckDuckGo or Serper
│   │   ├── fetch_page.py
│   │   ├── email.py            # SMTP send + IMAP poll
│   │   └── payment/
│   │       ├── __init__.py
│   │       ├── base.py         # PaymentProvider ABC
│   │       ├── mock.py
│   │       └── doku.py
│   ├── orchestrator.py
│   ├── websocket.py            # event streaming
│   ├── routes/
│   │   ├── campaigns.py
│   │   ├── leads.py
│   │   ├── runs.py
│   │   └── webhooks.py
│   └── tests/
│       └── test_pipeline.py    # CLI smoke test
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── pages/
│       │   ├── Dashboard.tsx
│       │   ├── CampaignNew.tsx
│       │   ├── CampaignRun.tsx     # the demo centerpiece
│       │   ├── Leads.tsx
│       │   └── LeadDetail.tsx
│       ├── components/
│       │   ├── AgentFeed.tsx        # live stream view
│       │   ├── DebatePanel.tsx      # Bull vs Bear vs Judge
│       │   ├── LeadKanban.tsx
│       │   └── PaymentTimeline.tsx
│       └── lib/
│           ├── api.ts
│           └── ws.ts
└── data/
    └── demo_leads.csv          # 3 demo leads for the recording
```

---

## 14. Pre-Build Checklist (Do Before Hour 0)

- [ ] Sumopod account active, AI credits visible, API key obtained
- [ ] Sumopod VPS template chosen and credits ready to allocate
- [ ] Sumopod AI dashboard checked — exact model IDs noted in `.env.example`
- [ ] DOKU developer account registered (sandbox credentials may arrive late — that's OK)
- [ ] Gmail account for the agent created, app password generated
- [ ] GitHub repo name decided: `OpenClaw2026_<TeamName>_Niaga`
- [ ] Devpost account created, team registered
- [ ] Cursor installed, signed in with hackathon credits
- [ ] Team roles agreed: who does backend, frontend, demo prep, pitch deck
- [ ] This document committed to repo as `/docs/BUILD_PLAN.md`

---

## 15. Single-Sentence North Star

> **By 23:00 WIB, a judge can open our live URL, click one button, and watch seven AI agents autonomously prospect, debate, qualify, email in Bahasa Indonesia, classify a reply, and close a deal with a DOKU payment link — all without any human clicks between start and finish.**

If a feature doesn't serve that sentence, cut it.
