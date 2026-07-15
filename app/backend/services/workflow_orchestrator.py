"""Task orchestrator - AI generate -> format -> SEO -> QA -> publish

Architecture (Phase 19):
    FastAPI request
        |
    asyncio background task
        |
    run_pipeline (AI generate + format + SEO + QA)
        |
    publish_queue.submit()  <-- serialized, safe, singleton browser
        |
    PublishQueue worker -> WeChat draft
"""

import asyncio
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from backend.services.ai import article_generator
from backend.services.content_optimizer import seo_optimizer, quality_checker, compliance_checker
from backend.database import get_db, TaskStatus


class PipelineStep(Enum):
    CREATED = ("created", "task created", 0)
    GENERATING = ("generating", "AI generating...", 20)
    FORMATTING = ("formatting", "formatting...", 30)
    SEO = ("seo", "SEO optimizing...", 50)
    CHECKING = ("checking", "quality checking...", 65)
    QUEUED = ("queued", "queued for publishing...", 75)
    PUBLISHING = ("publishing", "uploading to WeChat...", 85)
    DONE = ("done", "draft saved to WeChat!", 100)
    FAILED = ("failed", "failed", 0)

    def __init__(self, value, label, progress):
        self._value_ = value
        self.label = label
        self.progress = progress


@dataclass
class TaskState:
    task_id: str
    topic: str
    style: str
    author: str
    status: str = "created"
    progress: int = 0
    message: str = "task created"
    result: dict | None = None
    publish_task_id: str = ""


_tasks: dict[str, TaskState] = {}


def get_task_state(task_id):
    return _tasks.get(task_id)


def _update_state(task_id, step, **extra):
    if task_id in _tasks:
        _tasks[task_id].status = step.value
        _tasks[task_id].progress = step.progress
        _tasks[task_id].message = step.label
        for k, v in extra.items():
            setattr(_tasks[task_id], k, v)


async def run_pipeline(task_id, topic, style, length, author, template="knowledge"):
    """Main pipeline: AI generate -> format -> SEO -> QA -> queue publish.
    
    Now uses async task queue to avoid greenlet threading issues.
    """
    _tasks[task_id] = TaskState(task_id=task_id, topic=topic, style=style, author=author)
    db = get_db()

    try:
        # Step 1: AI generate
        _update_state(task_id, PipelineStep.GENERATING)
        logger.info("[Pipeline:{}] generating", task_id)
        article = await asyncio.to_thread(
            article_generator.generate, topic=topic, style=style, length=length
        )

        # Step 1.5: format
        _update_state(task_id, PipelineStep.FORMATTING)
        logger.info("[Pipeline:{}] formatting | template={}", task_id, template)
        try:
            from backend.services.content_formatter import format_article as fmt_a
            formatted = await asyncio.to_thread(
                fmt_a, article["title"], article["content_html"], author, template
            )
            article["title"] = formatted["title"]
            article["content_html"] = formatted["content_html"]
            article["summary"] = formatted["summary"]
            logger.success("[Pipeline:{}] formatted", task_id)
        except Exception as fe:
            logger.warning("[Pipeline:{}] format failed, continuing: {}", task_id, fe)

        # Step 2: SEO
        _update_state(task_id, PipelineStep.SEO)
        seo_result = await asyncio.to_thread(
            seo_optimizer.optimize, article["title"], article["content_html"], article.get("seo_keywords", "")
        )
        optimized_title = seo_result.get("optimized_title", article["title"])
        seo_description = seo_result.get("seo_description", article.get("summary", ""))

        # Step 3: QA
        _update_state(task_id, PipelineStep.CHECKING)
        quality = await asyncio.to_thread(
            quality_checker.check, optimized_title, article["content_html"]
        )
        compliance = await asyncio.to_thread(
            compliance_checker.check, optimized_title, article["content_html"]
        )
        logger.success("[Pipeline:{}] QA | score={} safe={}", task_id,
                       quality.get("score", 0), compliance.get("safe", False))

        # Step 4: Queue for publish (Phase 19: async queue, no daemon thread)
        _update_state(task_id, PipelineStep.QUEUED)
        logger.info("[Pipeline:{}] queueing publish", task_id)

        from backend.services.task_queue import publish_queue
        pub_task_id = await publish_queue.submit(
            title=optimized_title,
            content_html=article["content_html"],
            summary=seo_description,
            author=author,
        )
        _tasks[task_id].publish_task_id = pub_task_id
        _update_state(task_id, PipelineStep.PUBLISHING)

        # Poll publish queue status
        for _ in range(60):  # max 5 minutes
            await asyncio.sleep(5)
            pub_status = publish_queue.get_status(pub_task_id)
            if pub_status["status"] == "done":
                _update_state(task_id, PipelineStep.DONE, result={
                    "title": optimized_title,
                    "summary": seo_description,
                    "content_html": article["content_html"],
                    "seo_keywords": article.get("seo_keywords", ""),
                    "quality": quality,
                    "compliance": compliance,
                    "template": template,
                    "draft_id": pub_status.get("result", {}).get("draft_id", ""),
                }, message="draft saved to WeChat!")
                logger.success("[Pipeline:{}] done", task_id)
                db.create_article(topic=topic, style=style, title=optimized_title,
                                  summary=seo_description, content_html=article["content_html"],
                                  seo_keywords=article.get("seo_keywords", ""))
                return {"success": True, "data": _tasks[task_id].result}
            elif pub_status["status"] == "failed":
                _update_state(task_id, PipelineStep.FAILED,
                            message=f"publish failed: {pub_status.get('error', 'unknown')}")
                return {"success": False, "error": "PUBLISH_FAILED", "message": pub_status.get("error", "")}

        _update_state(task_id, PipelineStep.FAILED, message="publish timeout")
        return {"success": False, "error": "PUBLISH_TIMEOUT"}

    except Exception as e:
        logger.exception("[Pipeline:{}] exception", task_id)
        _update_state(task_id, PipelineStep.FAILED, message=str(e))
        return {"success": False, "error": str(e)}


def run_pipeline_async(task_id, topic, style, length, author, template="knowledge"):
    """Create an asyncio task (NOT a daemon thread) for the pipeline."""
    loop = asyncio.get_event_loop()
    return loop.create_task(
        run_pipeline(task_id, topic, style, length, author, template)
    )