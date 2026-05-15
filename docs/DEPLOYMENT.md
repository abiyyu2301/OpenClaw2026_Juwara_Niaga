# Deploying Niaga

Niaga is currently deployed to **Google Cloud Run** in the `niaga-496405` GCP project (region `asia-southeast2`, Jakarta).

**Live URL:** https://niaga-1029145238833.asia-southeast2.run.app

## Why Cloud Run

- Same GCP project as the Vertex AI Gemini credits Niaga already burns. One bill, one identity.
- Service account `niaga-backend` is attached directly to the service, so the container picks up Vertex AI auth from the metadata server — no JSON key on disk in production.
- WebSocket support is native (the live agent feed needs this).
- Scale-to-zero, then 1-2 instances during a demo — minimal cost.
- A single container serves both the FastAPI backend AND the built React frontend (the Dockerfile is multi-stage: `node:20-alpine` builds `frontend/dist`, then copies it into a `python:3.12-slim` runtime that mounts it at `/`).

## Re-deploy after a code change

From the repo root, with `gcloud` authenticated as a user that has Cloud Run + Cloud Build permissions (project owner or `roles/run.admin` + `roles/cloudbuild.builds.builder`):

```powershell
gcloud run deploy niaga `
  --source . `
  --region asia-southeast2 `
  --project niaga-496405 `
  --service-account niaga-backend@niaga-496405.iam.gserviceaccount.com `
  --allow-unauthenticated `
  --memory 1Gi `
  --timeout 600 `
  --max-instances 2 `
  --port 8080 `
  --quiet
```

What this does, end-to-end:

1. Uploads the repo to a Cloud Build staging bucket (`.dockerignore` keeps `credentials/`, `node_modules/`, `venv/`, etc. out).
2. Cloud Build builds the multi-stage container per `Dockerfile`. Takes 5-10 minutes the first time, 2-4 on subsequent builds (npm + pip layers cache).
3. Pushes the image to Artifact Registry (`asia-southeast2-docker.pkg.dev/niaga-496405/cloud-run-source-deploy/niaga`).
4. Creates a new Cloud Run revision, attaches the `niaga-backend` service account, sets IAM policy to allow unauthenticated public access, routes 100% traffic to the new revision.
5. Prints the Service URL.

## Prerequisites (first deploy only)

These were done already, but for reference:

```powershell
# 1. APIs (enabled via console while building)
gcloud services enable run.googleapis.com cloudbuild.googleapis.com `
  artifactregistry.googleapis.com cloudresourcemanager.googleapis.com `
  --project=niaga-496405

# 2. The service account exists with the Vertex AI User role
gcloud iam service-accounts describe niaga-backend@niaga-496405.iam.gserviceaccount.com `
  --project=niaga-496405

# 3. Cloud Build's default service account needs to be able to act as
#    niaga-backend for the deploy. The first `gcloud run deploy` auto-grants
#    this (roles/iam.serviceAccountUser) and you just confirm.
```

## What's in the container

| Layer | Source |
|---|---|
| `python:3.12-slim` base | Dockerfile |
| `pip install -r backend/requirements.txt` | Dockerfile stage 2 |
| `backend/` source | `COPY backend/ /app/backend/` |
| `frontend/dist/` built static files | `COPY --from=frontend /app/frontend/dist /app/frontend/dist` |
| Service account credentials | Attached to the Cloud Run service, NOT baked into the image |
| `.env` | Not in the image. Env vars set on the Cloud Run service (see below). |

## Setting environment variables on the service

For email / DOKU / etc. credentials, use Cloud Run env vars rather than the local `.env` file:

```powershell
gcloud run services update niaga --region asia-southeast2 --project niaga-496405 `
  --set-env-vars "GMAIL_ADDRESS=tim.niaga@gmail.com,GMAIL_APP_PASSWORD=<16-char-app-pw>"
```

For secrets, prefer Cloud Secret Manager:

```powershell
echo "<your-app-password>" | gcloud secrets create gmail-app-password --data-file=-
gcloud run services update niaga --region asia-southeast2 --project niaga-496405 `
  --set-secrets "GMAIL_APP_PASSWORD=gmail-app-password:latest"
```

`GCP_PROJECT_ID`, `GCP_LOCATION`, `GOOGLE_APPLICATION_CREDENTIALS` are NOT needed in production — Cloud Run + the attached service account handles auth.

## Cloud Run caveats to know before the demo

- **SQLite is ephemeral.** Cloud Run's filesystem is per-instance and resets on cold start. For the recording: hit the URL once to warm the container, create your campaign + leads, then record without long pauses. For real persistence, change `DATABASE_URL` to a Cloud SQL Postgres connection.
- **Cold start: ~30-60s** on first request after idle. Warm-instance latency is normal.
- **Single uvicorn worker per instance.** The orchestrator's in-memory background tasks (active run set, websocket hub) need shared state, which doesn't work across multiple workers. The `--max-instances 2` is enough headroom for one demo.
- **WebSocket timeout: 600s** (set via `--timeout`). Long-running orchestrator runs will hold the websocket open for the duration of a run; 10 min is plenty for a 3-lead demo.

## Smoke test the live URL

```powershell
# Backend health
curl https://niaga-1029145238833.asia-southeast2.run.app/api/health
# → {"status":"ok","service":"niaga"}

# Frontend
curl https://niaga-1029145238833.asia-southeast2.run.app/ | findstr "<title>"
# → <title>Niaga — Autonomous AI Sales Team</title>
```

Then open the URL in a browser and create a campaign. The `🔎 Find new leads` button uses Gemini with Google Search grounding to discover real Indonesian organizations matching your ICP.

## Tearing it down

If you want to stop incurring (very small) Cloud Run charges:

```powershell
gcloud run services delete niaga --region asia-southeast2 --project niaga-496405
```

The Artifact Registry images and Cloud Build logs persist; delete those manually if you want a clean slate:

```powershell
gcloud artifacts repositories delete cloud-run-source-deploy `
  --location=asia-southeast2 --project=niaga-496405
```

## Alternative: Sumopod VPS

The original 12-hour build plan called for Sumopod VPS hosting (Rp 36K/month). That path still works but was not used for this build. If you want to migrate from Cloud Run to Sumopod later, the steps are:

1. Provision a small Ubuntu 22.04 VPS (1 vCPU, 1 GB RAM).
2. `apt install python3.12 python3.12-venv nginx git nodejs`.
3. Clone the repo, `pip install` + `npm run build`.
4. Upload `credentials/niaga-backend-key.json` and set `GOOGLE_APPLICATION_CREDENTIALS` in `.env`.
5. Run uvicorn under systemd, with nginx reverse-proxying `/api/*`, `/ws/*`, and serving `frontend/dist/` for the rest.

The Cloud Run path above is the simpler one and removes the manual ops, so unless you have a reason to migrate, stay on Cloud Run.
