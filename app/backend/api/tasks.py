"""Task management API -- Phase 19: async pipeline"""

import uuid
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from loguru import logger
from backend.utils.exceptions import success_response, ErrorCode, AppError
from backend.database import get_db, TaskStatus
from backend.config import settings
from backend.services.workflow_orchestrator import (
    run_pipeline_async, get_task_state, PipelineStep, _tasks
)

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


class CreateTaskRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200, description="Article topic")
    style: str = Field(default="marketing", description="Style")
    length: str = Field(default="medium", description="Length")
    author: str = Field(default="wgzxhhh", description="Author")
    template: str = Field(default="knowledge", description="Format template")


@router.post("/create", summary="Create article task (one-click)")
async def create_task(req: CreateTaskRequest):
    """Submit a topic, trigger full pipeline: AI generate -> SEO -> QA -> publish draft"""
    task_id = str(uuid.uuid4())[:8]
    logger.info("Creating task | task_id={} topic={} style={}", task_id, req.topic, req.style)

    # Phase 19: asyncio task instead of daemon thread
    run_pipeline_async(task_id, req.topic, req.style, req.length, req.author, req.template)

    return success_response({
        "task_id": task_id,
        "status": "created",
        "message": "Task created, running in background...",
    })


@router.get("/{task_id}", summary="Check task status")
async def get_task(task_id: str):
    """Get real-time task progress"""
    state = get_task_state(task_id)
    if not state:
        raise AppError(ErrorCode.NOT_FOUND, f"Task not found: {task_id}", status_code=404)

    response = {
        "task_id": state.task_id,
        "status": state.status,
        "progress": state.progress,
        "message": state.message,
    }
    if state.result:
        response["result"] = state.result
    if state.publish_task_id:
        response["publish_task_id"] = state.publish_task_id

    return success_response(response)


@router.get("", summary="Task history")
async def list_tasks(
    status: str = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """View all previously generated articles"""
    db = get_db()
    articles = db.list_articles(status=status, limit=limit, offset=offset)
    counts = db.count_by_status()
    return success_response({
        "tasks": articles,
        "total": len(articles),
        "counts": counts,
    })