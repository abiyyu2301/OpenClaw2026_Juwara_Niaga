"""Niaga — FastAPI entrypoint.

Boots the API server, mounts WebSocket for the live agent feed, and exposes
campaign / lead / run / webhook routes.
"""

import os
from pathlib import Path

# CRITICAL: set GOOGLE_APPLICATION_CREDENTIALS before any google-auth import
# happens (settings, agents, anything). uvicorn launches with whatever the
# parent shell had set, which is typically nothing — so the auth library
# falls back to stale `gcloud auth` user creds and fails with invalid_grant.
def _seed_gcp_credentials() -> None:
    cur = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if cur and Path(cur).is_file():
        return
    here = Path(__file__).resolve().parent.parent
    for candidate in [
        here / "credentials" / "niaga-backend-key.json",
    ]:
        if candidate.is_file():
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(candidate)
            return


_seed_gcp_credentials()

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from db.session import Base, engine
from routes import campaigns as campaigns_routes
from routes import leads as leads_routes
from routes import runs as runs_routes
from routes import webhooks as webhooks_routes
from settings import settings
from websocket import run_socket
# Import models so SQLAlchemy registers them on Base.metadata before create_all.
from db import models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    from db.migrate import ensure_campaign_assets_table, migrate

    migrate(engine)
    ensure_campaign_assets_table(engine)
    yield


app = FastAPI(
    title="Niaga",
    description="Autonomous multi-agent B2B sales platform for Indonesian SMEs",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


API_PREFIX = "/api"
app.include_router(campaigns_routes.router, prefix=API_PREFIX)
app.include_router(leads_routes.router, prefix=API_PREFIX)
app.include_router(runs_routes.router, prefix=API_PREFIX)
app.include_router(webhooks_routes.router, prefix=API_PREFIX)


@app.get(f"{API_PREFIX}/health")
async def health():
    return {"status": "ok", "service": "niaga"}


@app.websocket("/ws/runs/{run_id}")
async def ws_run(websocket: WebSocket, run_id: int) -> None:
    """Live Agent Feed stream for an orchestrator run."""
    await run_socket(websocket, run_id)


# --- Static frontend (production) ---
# When `frontend/dist` exists (built via `npm run build`), serve it from `/`
# with SPA fallback. In local dev this directory is absent, so Vite serves
# the frontend on :5173 and proxies /api + /ws to this backend on :8000.
_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=str(_FRONTEND_DIST / "assets")),
        name="assets",
    )

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        # Internal endpoints win
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            return {"detail": "not found"}
        # Try serving a real file (e.g. /favicon.ico, /logo.svg)
        candidate = _FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))
        # SPA fallback
        return FileResponse(str(_FRONTEND_DIST / "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "name": "Niaga",
            "version": "0.1.0",
            "docs": "/docs",
            "health": f"{API_PREFIX}/health",
            "note": "frontend/dist not built — running API-only mode",
        }
