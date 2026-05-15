"""Run controller — start, pause, resume, stop autonomous runs."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.models import AgentMessage, AgentRun, Campaign
from db.session import get_db
from orchestrator import inbox_loop, pause_run, resume_run, run_campaign
from schemas import AgentMessageOut, RunOut

router = APIRouter(prefix="/runs", tags=["runs"])

_active_tasks: dict[int, list[asyncio.Task]] = {}


@router.post("/start", response_model=RunOut)
async def start_run(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    run = AgentRun(
        campaign_id=campaign_id,
        started_at=datetime.now(timezone.utc),
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Kick off the orchestrator + inbox loop as background tasks.
    main_task = asyncio.create_task(run_campaign(campaign_id, run.id))
    inbox_task = asyncio.create_task(inbox_loop(run.id))
    _active_tasks[run.id] = [main_task, inbox_task]
    return run


@router.post("/{run_id}/pause", response_model=RunOut)
def pause(run_id: int, db: Session = Depends(get_db)):
    run = db.query(AgentRun).get(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    pause_run(run_id)
    run.status = "paused"
    db.commit()
    return run


@router.post("/{run_id}/resume", response_model=RunOut)
def resume(run_id: int, db: Session = Depends(get_db)):
    run = db.query(AgentRun).get(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    resume_run(run_id)
    run.status = "running"
    db.commit()
    return run


@router.post("/{run_id}/stop", response_model=RunOut)
def stop(run_id: int, db: Session = Depends(get_db)):
    run = db.query(AgentRun).get(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    for t in _active_tasks.pop(run_id, []):
        t.cancel()
    run.status = "completed"
    run.ended_at = datetime.now(timezone.utc)
    db.commit()
    return run


@router.get("", response_model=list[RunOut])
def list_runs(db: Session = Depends(get_db)):
    return db.query(AgentRun).order_by(AgentRun.id.desc()).limit(50).all()


@router.get("/{run_id}", response_model=RunOut)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(AgentRun).get(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return run


@router.get("/{run_id}/messages", response_model=list[AgentMessageOut])
def get_run_messages(run_id: int, limit: int = 200, db: Session = Depends(get_db)):
    return (
        db.query(AgentMessage)
        .filter(AgentMessage.run_id == run_id)
        .order_by(AgentMessage.created_at.asc())
        .limit(limit)
        .all()
    )
