"""
Agent OS — FastAPI Server
Run with: uvicorn app.main:app --reload
Or:        python run.py --api
"""
import asyncio
import json
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent.core import agent
from app.agent.memory import agent_memory
from app.memory.episodic_store import episodic_store
from app.utils.logger import get_logger

logger = get_logger("main")

app = FastAPI(
    title="Agent OS",
    description="General Purpose Autonomous Agent OS",
    version="1.0.0",
    docs_url="/docs",
)


# ─── Schemas ──────────────────────────────────────────────────────────────────

class TaskRequest(BaseModel):
    goal: str
    verbose: bool = True


class TaskResponse(BaseModel):
    episode_id: str
    goal: str
    final_output: str
    success: bool
    duration_seconds: float
    stats: Dict[str, Any]


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"name": "Agent OS", "version": "1.0.0", "status": "operational"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/run", response_model=TaskResponse)
async def run_task(req: TaskRequest):
    """Run a task synchronously and return the final result."""
    try:
        result = agent.run(req.goal, verbose=req.verbose)
        return TaskResponse(
            episode_id=result["episode_id"],
            goal=result["goal"],
            final_output=result["final_output"],
            success=result["success"],
            duration_seconds=result["duration_seconds"],
            stats=result["stats"],
        )
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/stream")
async def stream_task(req: TaskRequest):
    """Stream task progress as Server-Sent Events."""

    async def generate():
        for event in agent.stream(req.goal):
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0)

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/memory/stats")
async def memory_stats():
    return agent_memory.get_stats()


@app.get("/memory/recent")
async def recent_episodes(n: int = 5):
    return episodic_store.get_recent(n)


@app.delete("/memory/working")
async def clear_working():
    agent_memory.clear_working()
    return {"message": "Working memory cleared"}
