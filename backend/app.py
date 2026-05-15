"""Niaga — FastAPI entrypoint.

Boots the API server, mounts WebSocket for the live agent feed, and exposes
campaign / lead / run / webhook routes.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from db.session import Base, engine
from settings import settings
from websocket import run_socket
# Import models so SQLAlchemy registers them on Base.metadata before create_all.
from db import models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
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


@app.get("/health")
async def health():
    return {"status": "ok", "service": "niaga"}


@app.get("/")
async def root():
    return {
        "name": "Niaga",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.websocket("/ws/runs/{run_id}")
async def ws_run(websocket: WebSocket, run_id: int) -> None:
    """Live Agent Feed stream for an orchestrator run."""
    await run_socket(websocket, run_id)
