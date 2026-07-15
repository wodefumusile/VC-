"""Async publish task queue -- serializes WeChat publish operations.

All Playwright Sync API calls stay within a single thread via
playwright_service.run_with_page().
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

from publish_engine.core.playwright_service import playwright_service
from publish_engine.wechat.article import WechatArticle


class PublishStatus(Enum):
    QUEUED = "queued"
    PUBLISHING = "publishing"
    DONE = "done"
    FAILED = "failed"


@dataclass
class PublishTask:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    content_html: str = ""
    summary: str = ""
    author: str = "wgzxhhh"
    status: str = "queued"
    result: dict | None = None
    error: str = ""

    def to_article(self) -> WechatArticle:
        return WechatArticle(
            title=self.title,
            content=self.content_html,
            summary=self.summary,
            author=self.author,
        )


class PublishQueue:
    """Async queue that serializes all WeChat publish operations."""

    def __init__(self):
        self._queue: asyncio.Queue[PublishTask] = asyncio.Queue(maxsize=50)
        self._worker_task: asyncio.Task | None = None
        self._tasks: dict[str, PublishTask] = {}
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        if self._worker_task and not self._worker_task.done():
            return
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("PublishQueue worker started")

    async def stop(self) -> None:
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("PublishQueue worker stopped")

    async def submit(self, title: str, content_html: str, summary: str = "", author: str = "wgzxhhh") -> str:
        task = PublishTask(title=title, content_html=content_html, summary=summary, author=author)
        self._tasks[task.task_id] = task
        await self._queue.put(task)
        logger.info("PublishQueue submitted | id={} title={}", task.task_id, title[:30])
        return task.task_id

    def get_status(self, task_id: str) -> dict:
        task = self._tasks.get(task_id)
        if not task:
            return {"task_id": task_id, "status": "not_found", "error": "task not found"}
        return {
            "task_id": task.task_id,
            "status": task.status,
            "result": task.result,
            "error": task.error,
        }

    async def _worker(self) -> None:
        logger.info("PublishQueue worker running")
        while True:
            try:
                task = await self._queue.get()
                await self._publish_one(task)
                self._queue.task_done()
            except asyncio.CancelledError:
                logger.info("PublishQueue worker cancelled")
                break
            except Exception as e:
                logger.exception("PublishQueue worker error: {}", e)

    async def _publish_one(self, task: PublishTask) -> None:
        """Execute a single publish operation. All PLAYWATT in one thread."""
        async with self._lock:
            task.status = PublishStatus.PUBLISHING.value
            logger.info("PublishQueue executing | id={}", task.task_id)

            article = task.to_article()

            def _do_publish(page):
                from publish_engine.auth.login import start_login
                from publish_engine.wechat.editor import WechatEditor

                login_result = start_login(page, timeout=120)
                if not login_result["success"]:
                    return {"success": False, "error": "login expired"}

                editor = WechatEditor(page)
                return editor.publish_draft(article)

            try:
                result = await playwright_service.run_with_page(_do_publish)

                if result.get("success"):
                    task.status = PublishStatus.DONE.value
                    task.result = {
                        "draft_id": result.get("draft_id", ""),
                        "message": result.get("message", ""),
                    }
                    await playwright_service.save_auth()
                    logger.success("PublishQueue done | id={}", task.task_id)
                else:
                    task.status = PublishStatus.FAILED.value
                    task.error = result.get("error", "unknown error")
                    logger.warning("PublishQueue failed | id={} msg={}", task.task_id, task.error)

            except Exception as e:
                task.status = PublishStatus.FAILED.value
                task.error = str(e)
                logger.exception("PublishQueue error | id={}", task.task_id)


publish_queue = PublishQueue()