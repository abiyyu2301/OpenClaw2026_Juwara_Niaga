# Niaga — Build Progress & Handoff

Live status doc updated as each phase ships. If a new Claude session picks this up, read this file first, then `docs/BUILD_PLAN.md` for the full architecture.

## Current state at a glance

- **Live URL**: https://niaga-1029145238833.asia-southeast2.run.app ← paste this in Devpost
- **Repo**: https://github.com/abiyyu2301/OpenClaw2026_Juwara_Niaga (public)
- **Local**: `C:\Users\abiyy\OpenClaw2026_Juwara_Niaga`
- **GCP**: project `niaga-496405`, Vertex AI enabled, service account `niaga-backend@niaga-496405.iam.gserviceaccount.com`, JSON key at `credentials/niaga-backend-key.json`
- **Cloud Run service**: `niaga` in region `asia-southeast2` (Jakarta), revision `niaga-00001-w7p`
- **Auth**: gh CLI logged in as `abiyyu2301`; gcloud logged in as abiyyu.avicena23@gmail.com
- **Runtime LLM**: Google Gemini via Vertex AI (~$1,150 of credits)
- **Models**: `gemini-2.5-flash` (Prospector/Bull/Bear/Reply/AfterCare) + `gemini-2.5-pro` (Judge/Outreach/Closer/LeadFinder)
- **LeadFinder**: gemini-2.5-pro with Google Search grounding — discovers real Indonesian SMEs matching the ICP

## Cloud Run notes
- SQLite is ephemeral on Cloud Run (file system is per-instance). On cold start the DB resets. For a persistent demo, either keep the service warm with one request before the recording, OR migrate to Cloud SQL for Postgres (set DATABASE_URL).
- Cold start: ~30-60s on first request after idle. Warm: instant.
- Single uvicorn worker per instance (background tasks need shared state). Max instances: 2.
- Service account `niaga-backend` runs the container — picks up Vertex AI auth via the metadata server, no JSON key needed in the deployment.

## Re-deploy

After any code change:
```bash
cd C:\Users\abiyy\OpenClaw2026_Juwara_Niaga
gcloud run deploy niaga --source . --region asia-southeast2 --project niaga-496405 \
  --service-account niaga-backend@niaga-496405.iam.gserviceaccount.com \
  --allow-unauthenticated --memory 1Gi --timeout 600 --max-instances 2 --port 8080 --quiet
```
Takes ~5-10 minutes for a multi-stage Docker build (npm + pip).

## Phase status

| Phase | Window | Status |
|---|---|---|
| 0 Lock & Load | 09:45–10:15 | ✅ DONE |
| 1 Core agents (Prospector, Bull, Bear, Judge) | 11:45–14:30 | ✅ DONE |
| 2 Outreach + Reply + email + orchestrator | 14:30–16:30 | ✅ DONE |
| 3 Closer + AfterCare + payment provider + webhook | 16:30–18:30 | ✅ DONE |
| 4 Demo UX (live feed, kanban, debate panel, campaign UI) | 18:30–20:00 | ✅ DONE |
| 5 Demo prep (seed CSV, deploy guide) | 20:00–21:30 | ✅ DONE |
| 6 Pitch deck + Devpost submission content | 21:30–23:00 | ✅ DONE |

## Remaining work — handed off to you (the user) for final submission

These are the steps Claude can't do (require your phone, payment, video recording, manual upload):

1. ~~Deploy~~ ✅ Niaga is live on Google Cloud Run at https://niaga-1029145238833.asia-southeast2.run.app. To re-deploy after changes, see `docs/DEPLOYMENT.md`.
2. **Record the demo video** — use the script in `docs/SUBMISSION.md`. Run against the live URL (warm it with one request first to avoid the cold-start), screen-record, narrate. Target 1:50. Upload to YouTube as **Unlisted**.
3. **Build the 5-slide PDF deck** — copy content from `docs/PITCH_DECK.md` into Google Slides → export as `OpenClaw2026_Juwara_Niaga.pdf`.
4. **Devpost submission form** — paste the narrative from `docs/SUBMISSION.md`, upload deck + paste video URL + paste GitHub + paste live URL, check **Best Payment Use Case** label, submit before 23:00 WIB May 15.

## The backend is feature-complete

End-to-end test (`backend/tests/test_webhook.py`) verifies the complete autonomous loop with zero human intervention:

```
new lead -> Prospector (gemini-2.5-flash, 0 thinking)
         -> Bull || Bear (parallel, gemini-2.5-flash, 0 thinking)
         -> Judge verdict (gemini-2.5-pro, thinking=1024)  -> QUALIFIED, fit 85
         -> Outreach (BI email, gemini-2.5-pro, thinking=768) -> dry-run sent
synthetic pricing-question reply injected
         -> Reply (gemini-2.5-flash, 0 thinking) -> pricing_question, positive
         -> Closer (gemini-2.5-pro, thinking=1024) -> workshop_booking Rp 500,000
         -> MockPaymentProvider -> http://localhost:5173/mock-pay/<ref>
         -> follow-up BI email sent (dry-run)
mock-pay webhook fires status=paid
         -> payment_events.payment_status = paid
         -> lead.status = paid, run.deals_closed += 1, total_revenue += 500_000
         -> AfterCare (gemini-2.5-flash) -> "Pembayaran Workshop Anda Telah Berhasil!"
```

Total cost per closed deal in tokens: ~5,000 in / ~2,000 out across 8 agent calls ≈ **$0.10 per deal at Gemini 2.5 Flash + Pro pricing**. Well under the $1,150 GCP budget.

## What's been done

### Phase 0 deliverables (all shipping)
- FastAPI backend with `/health` + WebSocket `/ws/runs/{id}` (echo)
- 9 SQLAlchemy models matching build plan §6
- `backend/agents/llm.py` Vertex AI Gemini wrapper (native JSON mode, retry, token capture)
- `backend/agents/base.py` BaseAgent class (prompt loading, LLM call, event logging, WebSocket broadcast)
- React + Vite + Tailwind frontend with Niaga palette (terracotta + sandstone)
- Dashboard route that probes `/api/health`
- Smoke test passes: Gemini returns `{'greeting': 'Halo', 'ready_to_build': True}` in 2.8s

### Phase 1 deliverables (all shipping)
- BaseAgent class (prompt loading, LLM call, evidence-locker logging, WebSocket broadcast)
- 4 prompt templates: prospector/bull/bear/judge
- 4 agent classes
- test_pipeline.py runs Prospector → (Bull || Bear) → Judge on a demo lead and prints all messages

### End-to-end test result
On the demo lead "PT Mitra Edukasi Nusantara" (corporate training, ICP-fit):
- Prospector → fit 85, High confidence, surfaced the "sales admin job opening" trigger
- Bull → Rp 36M deal value, high urgency, 3 specific arguments (no generic SDR fluff)
- Bear → 75% disqualifier probability, valid counter-arguments (e.g. "the sales admin job opening could mean they want a HUMAN, not AI")
- Judge → QUALIFIED, fit 85, High confidence, sales-coach-quality reasoning, recommended pilot Rp 36M
- Total: 2,744 in / 1,110 out tokens across 4 agents → ~$0.05-0.10 per lead at Gemini 2.5 Flash + Pro pricing

### Lessons learned (read before continuing)
- **Gemini 2.5 thinking models share `max_output_tokens` between thinking + visible output.** With small caps and thinking enabled, the visible response gets truncated. Default `default_thinking_budget = 0` for cheap agents (Prospector/Bull/Bear/Reply/AfterCare). Judge/Outreach/Closer use thinking + bigger output cap.
- google-genai 0.3.0 lacked ThinkingConfig → upgraded to 2.3.0 in requirements.txt.
- The `name` attribute on each agent must match its prompt filename AND the `MODEL_<NAME>` env var key in settings.py.

### Commits
```
(Phase 1 commits — see git log)
91206a2 Phase 0 verification: fix pydantic namespace warning, ASCII test output
bb07284 Frontend scaffold: React + Vite + Tailwind with Niaga palette
d2812f0 Backend scaffold: FastAPI, SQLAlchemy models, Gemini LLM wrapper
1816e9d Initial repo: README, build plan, env template, license
```

## Resume instructions (if session ends)

1. `cd C:\Users\abiyy\OpenClaw2026_Juwara_Niaga`
2. Activate venv: `.\backend\venv\Scripts\activate`
3. Check what's next in this file
4. Continue from the current in-progress phase

If smoke test breaks, run `python backend\tests\test_gemini_smoke.py` to diagnose. If GCP creds are stale, regenerate the JSON key in the GCP console and replace `credentials/niaga-backend-key.json`.

## Known issues / decisions log

- DOKU MCP server credentials require a 15-30 min consultation booking, so we ship `MockPaymentProvider` as the primary demo path with the real DOKU adapter as a fallback. Form submitted: https://forms.doku.com/agentic-payments
- Pivoted from the original Sumopod VPS plan to Google Cloud Run. Same GCP project as the Vertex AI Gemini credits, attached service account auth (no JSON key in production), native WebSocket support, scale-to-zero. Sumopod VPS path documented as an alternative in `docs/DEPLOYMENT.md`.
- Test of `gemini-2.5-pro` with `max_output_tokens=80` returned empty text — the thinking budget consumed the entire output cap. **For premium-tier agents, allocate ≥800 max_output_tokens.**
- Pydantic v2 protected namespaces: settings.py uses `protected_namespaces=()` so `model_*` field names don't warn.
- Windows console encoding: avoid Unicode arrows/checkmarks in print statements (cp1252 charmap doesn't have them).
