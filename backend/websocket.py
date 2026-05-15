"""WebSocket hub for the Live Agent Feed.

Each `run_id` has its own room. Broadcasts go to all subscribers of that room.
For the Phase 0 skeleton, this is an echo server; real event streaming wires
up in Phase 2 alongside the orchestrator.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Dict, Set

from fastapi import WebSocket, WebSocketDisconnect


class WSHub:
    def __init__(self) -> None:
        self._rooms: Dict[int, Set[WebSocket]] = defaultdict(set)

    async def join(self, run_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self._rooms[run_id].add(ws)

    def leave(self, run_id: int, ws: WebSocket) -> None:
        self._rooms[run_id].discard(ws)
        if not self._rooms[run_id]:
            self._rooms.pop(run_id, None)

    async def broadcast(self, run_id: int, payload: dict) -> None:
        message = json.dumps(payload)
        dead: list[WebSocket] = []
        for ws in self._rooms.get(run_id, ()):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.leave(run_id, ws)


hub = WSHub()


async def run_socket(websocket: WebSocket, run_id: int) -> None:
    """Connect a client to the live feed for `run_id`. Currently echoes any
    inbound message back — useful for the Phase 0 smoke test."""
    await hub.join(run_id, websocket)
    try:
        await hub.broadcast(
            run_id,
            {"agent": "system", "role": "thought", "content": f"connected to run {run_id}"},
        )
        while True:
            data = await websocket.receive_text()
            await hub.broadcast(
                run_id,
                {"agent": "echo", "role": "message_out", "content": data},
            )
    except WebSocketDisconnect:
        hub.leave(run_id, websocket)
