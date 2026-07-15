"""Publish API -- Phase 19: async queue with thread-safe Playwright"""

import sys
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel, Field
from loguru import logger
from backend.utils.exceptions import success_response, ErrorCode, AppError

router = APIRouter(prefix="/api/publish", tags=["Publish to WeChat"])


class PublishDraftRequest(BaseModel):
    title: str = Field(..., min_length=1)
    summary: str = Field(default="")
    content_html: str = Field(..., min_length=1)
    author: str = Field(default="wgzxhhh")


@router.post("/draft", summary="Upload draft to WeChat")
async def publish_draft(req: PublishDraftRequest):
    logger.info("======== WeChat Publish ========")
    logger.info("Title: {}", req.title[:60])
    logger.info("Author: {}", req.author)
    logger.info("HTML Len: {}", len(req.content_html))
    logger.info("================================")

    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from backend.services.task_queue import publish_queue

    task_id = await publish_queue.submit(
        title=req.title,
        content_html=req.content_html,
        summary=req.summary,
        author=req.author,
    )

    import asyncio
    for _ in range(30):
        await asyncio.sleep(10)
        status = publish_queue.get_status(task_id)
        if status["status"] == "done":
            logger.success("Draft published: {}", task_id)
            return success_response({
                "draft_id": status.get("result", {}).get("draft_id", ""),
                "message": "Draft saved!",
                "task_id": task_id,
            })
        elif status["status"] == "failed":
            raise AppError(ErrorCode.INTERNAL_ERROR, status.get("error", "Unknown error"), status_code=500)

    raise AppError(ErrorCode.INTERNAL_ERROR, "Publish timeout", status_code=504)