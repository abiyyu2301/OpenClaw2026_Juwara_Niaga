# Devpost Submission Checklist — Team Juwara · Niaga

Per the Official Technical Guidelines and the Devpost form fields.

## What goes where

| Devpost field | Source |
|---|---|
| **Project Name** | `Niaga — Autonomous AI Sales Team` (or just `Niaga`) |
| **Tagline** | `Autonomous multi-agent B2B sales platform for Indonesian SMEs.` |
| **Project Description** | See "Project description (narrative)" below |
| **What it does** | "Define ICP + offer once. Niaga prospects, debates each lead adversarially (Bull vs Bear vs Judge), drafts Bahasa Indonesia outreach, sends email, classifies replies, decides on a DOKU payment link, and onboards on payment success — zero human clicks." |
| **Built with** | Python, FastAPI, Google Gemini (Vertex AI), React, Vite, Tailwind, SQLAlchemy, WebSocket, Gmail SMTP/IMAP, DOKU Payment Link |
| **Try it out (links)** | GitHub: `https://github.com/abiyyu2301/OpenClaw2026_Juwara_Niaga` · **Live: `https://niaga-1029145238833.asia-southeast2.run.app`** |
| **Video** | Upload to YouTube as **UNLISTED** (per Official Technical Guidelines — note: Devpost EN page says Public, but the ID guidelines doc overrides) · file name `OpenClaw2026_Juwara_Niaga.mp4` |
| **Pitch deck** | `OpenClaw2026_Juwara_Niaga.pdf` (5 slides max, from `docs/PITCH_DECK.md`) |
| **AI Tools / Models Used** | "Google Gemini 2.5 Flash (Prospector, Bull, Bear, Reply, AfterCare) and Gemini 2.5 Pro (Judge, Outreach, Closer) via Vertex AI on Google Cloud. All agents return native JSON. Cursor IDE used as the development assistant during the 12-hour build." |
| **Sponsor / Special Prizes** | ✅ Check **Best Payment Use Case** (DOKU track) |

## Project description (narrative — paste in Devpost)

> ### What it does
> Niaga is an autonomous AI sales team built for Indonesian SMEs. You define an Ideal Customer Profile and an offer one time. From there, seven specialized agents collaborate in a deterministic orchestrator loop:
>
> 1. **Prospector** enriches each raw lead with structured fit-score reasoning
> 2. **Bull** argues for pursuing the lead
> 3. **Bear** argues against
> 4. **Judge** renders an explainable verdict citing both sides
> 5. **Outreach** drafts a warm, formal Bahasa Indonesia first-touch email
> 6. **Reply** classifies any inbound response by intent and sentiment
> 7. **Closer** decides whether to send a DOKU payment link, which type (deposit / pilot fee / workshop booking), and what amount, then sends the follow-up email
>
> An **AfterCare** agent fires automatically when a DOKU payment webhook arrives with `status=paid`, sending a warm Bahasa Indonesia onboarding email confirming the booking and outlining next steps.
>
> Throughout, every agent action — every thought, tool call, tool result, decision — is written to an `agent_messages` evidence locker AND streamed live over a WebSocket to a 3-column dashboard that shows the lead kanban, the live agent feed, and the Bull-vs-Bear-vs-Judge debate side by side. Judges watch the autonomy happen.
>
> ### Why this wins
> - **Adversarial qualification is the differentiator.** Bull/Bear/Judge produces *explainable* fit scores. Other tools say "lead score: 78"; we cite the actual arguments on both sides.
> - **DOKU as a commercial event, not a pay button.** The Closer picks the right type of payment for the deal — a refundable consultation deposit, a workshop booking, a paid trial — based on the prospect's stated intent.
> - **Bahasa Indonesia native.** Gemini 2.5 Pro produces outreach prose that reads as warm formal BI, not translated English. The "Halo, semoga Ibu dalam keadaan sehat" tone is critical for Indonesian B2B etiquette.
> - **End-to-end autonomy.** Zero human clicks from `new` to `paid`. The orchestrator loop is the autonomous component the competition rules require, and the `agent_messages` table is the evidence.
>
> ### How we built it
> Plain async Python on FastAPI (no LangGraph — the 12-hour clock punishes framework overhead). SQLAlchemy models matching the 9-table schema in the build plan. Vertex AI Gemini 2.5 Flash for cheap-tier agents and 2.5 Pro for the premium decisions (Judge, Outreach, Closer). React + Vite + Tailwind for the live UI with an Indonesian-inspired terracotta-and-sandstone palette. Gmail SMTP for sending and IMAP polling for replies. A `PaymentProvider` ABC with a `MockPaymentProvider` first-class implementation (because real DOKU sandbox credentials require a 15-30 min consultation booking we submitted but couldn't expect to come back in 12 hours) and a `DOKUPaymentProvider` against the Checkout API with HMAC-SHA256 signature verification.
>
> ### Challenges we ran into
> - **Gemini 2.5 thinking models share `max_output_tokens` between thinking and visible output.** Small caps left visible JSON truncated. Fix: agent-level `thinking_budget` (0 for cheap classification agents, 1024 for Judge/Closer where reasoning matters).
> - **DOKU MCP credentials require a consultation booking** — not a 12-hour-friendly process. Built mock + real implementations behind the same interface so the demo runs on the mock and a real-credential swap is a one-line config change.
> - **Windows console encoding (cp1252)** crashed on Unicode arrows in test output. Stuck to ASCII glyphs.
>
> ### What's next
> WhatsApp Business channel · LinkedIn warming via Repliz · Javanese/Sundanese localization · QRIS + Virtual Account + e-wallet via DOKU's full Checkout surface · RAG over the merchant's CRM history.

## Demo video script (≤ 2:00, target 1:50)

| Time | Scene | What's said / shown |
|---|---|---|
| 0:00–0:12 | Title card + problem | "Indonesian SMEs lose deals because sales is a manual chat thread. Global AI tools aren't built for our market." |
| 0:12–0:25 | Campaign setup form | Show the New Campaign page. ICP = Jakarta corporate training providers. Offer = Niaga pilot at Rp 3M/month. Click **Create campaign** with the 3-lead seed checked. |
| 0:25–0:35 | Campaign Run page loads | "Three demo leads. One strong fit, one weak fit, one ambiguous. Watch what happens." Hover the **Start Autonomous Run** button. |
| 0:35–1:10 | **Live agent feed plays** | Click **Start Autonomous Run**. Narration: "Prospector researches each company in real time. Then watch this — Bull builds the case FOR, Bear builds the case AGAINST, in parallel. The Judge weighs both and renders a verdict." On screen: terminal feed scrolls, kanban tiles transition from `new` to `profiling` to `debating` to `qualified` / `disqualified`. Highlight the disqualified MLM lead — "Niaga says no when it should say no." |
| 1:10–1:25 | Bahasa Indonesia email + reply | Click into the strong-fit lead. Show the drafted email in the debate panel — warm formal BI, references the specific trigger from the profile. Cut to inbox: prospect replied asking pricing. Show Reply agent classifying live: `pricing_question, positive sentiment`. |
| 1:25–1:45 | **DOKU close** | "The Closer agent decides — workshop booking deposit, Rp 500,000." Show payment link generated. Click **Mark as paid** simulator button. Webhook fires. AfterCare agent draft: "Pembayaran Workshop Anda Telah Berhasil!" |
| 1:45–2:00 | Dashboard tally | Cut back to dashboard. "Three leads processed. One disqualified. One closed. Rp 500,000 collected. Zero human clicks between start and finish." End on the Niaga logo + GitHub URL. |

## Final pre-submit verification

- [ ] GitHub repo is **public** (not private)
- [ ] README has working setup instructions
- [ ] `.env.example` is committed; **`.env` and `credentials/` are NOT**
- [ ] Commit history is spread across the 12-hour window (no end-of-day giant push)
- [ ] Video file naming: `OpenClaw2026_Juwara_Niaga.mp4` → uploaded YouTube **Unlisted**
- [ ] Deck file naming: `OpenClaw2026_Juwara_Niaga.pdf` → max 5 slides
- [ ] Devpost team naming: `OpenClaw2026_Juwara`
- [ ] **Best Payment Use Case** label selected on Devpost
- [ ] Live deployment URL (Sumopod) tested in incognito (no auth wall)
- [ ] Project Description filled in with the narrative above
- [ ] AI Tools / Models Used filled with the specific Gemini IDs per agent
