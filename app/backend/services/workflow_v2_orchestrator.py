"""V2 Workflow Orchestrator — full v2.1 pipeline.

Independent from v1.0 workflow_orchestrator.
Enables both v1 and v2 to run independently.

Pipeline (v2.1):
  Input topic
    → Knowledge Enhancer (optional, v2.1 new)
    → AI Generate (DeepSeek)
    → Image Plan (ImagePlanner Agent)
    → Image Generate (ImageProvider → 即梦)
    → Format (FormatterEngine v2, section+span)
    → SEO + Compliance (v1 modules)
    → Quality Check (QualityCheckerV2)
    → Publish Queue → WeChat Draft
"""

import asyncio
import time
from loguru import logger

from backend.config import settings
from backend.services.ai import article_generator
from backend.services.image_agent import image_planner
from backend.services.image_provider import get_image_provider
from backend.services.formatter_engine import format_article
from backend.services.content_optimizer import seo_optimizer, quality_checker, compliance_checker
from backend.services.quality_checker_v2 import quality_checker_v2
from backend.database import get_db


class V2PipelineSteps:
    KNOWLEDGE = "knowledge"        # v2.1 new
    CREATED = "created"
    GENERATING = "generating"
    IMAGE_PLANNING = "image_planning"
    IMAGE_GENERATING = "image_generating"
    FORMATTING = "formatting"
    SEO = "seo"
    CHECKING = "checking"
    QUALITY_V2 = "quality_v2"
    PUBLISHING = "publishing"
    DONE = "done"
    FAILED = "failed"


def _enhance_with_knowledge(topic: str) -> str | None:
    """Knowledge Enhancer: 从知识库检索相关内容，注入上下文。

    仅在 settings.obsidian_enabled 为 True 时执行。
    """
    if not settings.obsidian_enabled:
        logger.info("[Knowledge] skipped — OBSIDIAN_PATH not set or ENABLE_KNOWLEDGE=false")
        return None

    try:
        from backend.services.knowledge_engine import KeywordJaccardRetriever
        retriever = KeywordJaccardRetriever(settings.OBSIDIAN_PATH)
        results = retriever.search(topic, top_k=3)

        if not results:
            logger.info("[Knowledge] no matches found for topic: {}", topic)
            return None

        logger.info("[Knowledge] found {} relevant docs | top={} score={:.2f}",
                     len(results), results[0].title[:40], results[0].score)

        # 构建知识上下文注入
        context_parts = ["## 相关知识库内容\n"]
        for i, r in enumerate(results, 1):
            context_parts.append(f"### {i}. {r.title}")
            context_parts.append(f"来源: {r.source}")
            context_parts.append(r.content[:1000])
            context_parts.append("")

        knowledge_context = "\n".join(context_parts)
        return knowledge_context

    except Exception as e:
        logger.warning("[Knowledge] failed: {} — continuing without knowledge", e)
        return None


async def run_v2_pipeline(
    topic: str,
    style: str = "marketing",
    length: str = "medium",
    author: str = "wgzxhhh",
    template: str = "knowledge",
) -> dict:
    """Run the complete v2.1 pipeline.

    Returns:
        {success: bool, data: {...} | error: str}
    """
    db = get_db()
    logger.info("[V2Pipeline] start | topic={} style={}", topic, style)

    try:
        # Step 0: Knowledge Enhancer (v2.1 new, optional)
        knowledge_context = _enhance_with_knowledge(topic)

        # Step 1: AI Generate (enriched with knowledge if available)
        logger.info("[V2Pipeline] step 1/7: generating article")
        enhanced_topic = topic
        if knowledge_context:
            enhanced_topic = f"{topic}\n\n{knowledge_context}"
            logger.info("[V2Pipeline] knowledge context appended | len={}", len(knowledge_context))

        article = article_generator.generate(
            topic=enhanced_topic, style=style, length=length,
        )
        db_article = db.create_article(
            topic=topic, style=style,
            title=article["title"],
            summary=article["summary"],
            content_html=article["content_html"],
            seo_keywords=article.get("seo_keywords", ""),
        )
        article_id = db_article["id"]

        # Step 2: Image Planning
        if settings.image_enabled:
            logger.info("[V2Pipeline] step 2/7: planning images")
            image_plan = image_planner.plan(
                title=article["title"],
                content=article["content_html"],
                category=style,
            )

            # Step 3: Image Generation
            logger.info("[V2Pipeline] step 3/7: generating images")
            provider = get_image_provider()
            image_records = []

            # Cover image
            if image_plan.get("cover", {}).get("prompt"):
                cover_prompt = image_plan["cover"]["prompt"]
                rec = db.create_image_record(
                    article_id=article_id, prompt=cover_prompt,
                    position=0, image_type="cover", provider=provider.name,
                )
                db.update_image_record(rec["id"], status="generating")

                result = provider.generate(cover_prompt)
                if result.success:
                    db.update_image_record(rec["id"], status="generated",
                                           image_url=result.image_url, task_id=result.task_id)
                else:
                    db.update_image_record(rec["id"], status="failed",
                                           error_message=result.error)
                image_records.append(db.get_image_record(rec["id"]))

            # Body illustrations
            for img in image_plan.get("images", []):
                prompt = img.get("prompt", "")
                if not prompt:
                    continue
                rec = db.create_image_record(
                    article_id=article_id, prompt=prompt,
                    position=img.get("position", len(image_records)),
                    image_type="illustration", provider=provider.name,
                )
                db.update_image_record(rec["id"], status="generating")

                result = provider.generate(prompt)
                if result.success:
                    db.update_image_record(rec["id"], status="generated",
                                           image_url=result.image_url, task_id=result.task_id)
                else:
                    db.update_image_record(rec["id"], status="failed",
                                           error_message=result.error)
                image_records.append(db.get_image_record(rec["id"]))

            logger.info("[V2Pipeline] images generated | total={} ok={}",
                         len(image_records),
                         sum(1 for r in image_records if r["status"] == "generated"))
        else:
            logger.info("[V2Pipeline] image steps skipped — IMAGE_API_KEY not set or ENABLE_IMAGE=false")
            image_records = []

        # Step 4: Format (v2 FormatterEngine)
        logger.info("[V2Pipeline] step 4/7: formatting with template={}", template)
        formatted = format_article(
            title=article["title"],
            content=article["content_html"],
            author=author,
            template=template,
            images=[r for r in image_records if r.get("image_url")],
        )

        # Step 5: SEO + Compliance (v1 modules)
        logger.info("[V2Pipeline] step 5/7: SEO + compliance")
        seo_result = seo_optimizer.optimize(
            formatted["title"], formatted["content_html"],
            article.get("seo_keywords", ""),
        )
        compliance = compliance_checker.check(
            formatted["title"], formatted["content_html"],
        )

        # Step 6: Quality Check V2
        logger.info("[V2Pipeline] step 6/7: quality check v2")
        qc_result = quality_checker_v2.check(
            title=formatted["title"],
            content_html=formatted["content_html"],
            images=image_records,
        )

        if qc_result["status"] == "fail":
            logger.warning("[V2Pipeline] quality check FAILED | score={}", qc_result["score"])
            return {
                "success": False,
                "error": f"Quality check failed (score={qc_result['score']})",
                "quality": qc_result,
            }

        # Step 7: Publish
        logger.info("[V2Pipeline] step 7/7: queuing publish")
        from backend.services.task_queue import publish_queue
from __future__ import annotations
        pub_task_id = await publish_queue.submit(
            title=seo_result.get("optimized_title", formatted["title"]),
            content_html=formatted["content_html"],
            summary=seo_result.get("seo_description", formatted["summary"]),
            author=author,
        )

        result = {
            "title": formatted["title"],
            "summary": formatted["summary"],
            "content_html": formatted["content_html"],
            "seo_keywords": article.get("seo_keywords", ""),
            "seo": seo_result,
            "compliance": compliance,
            "quality": qc_result,
            "images": image_records,
            "template": template,
            "publish_task_id": pub_task_id,
            "knowledge_used": knowledge_context is not None,
        }

        logger.success("[V2Pipeline] DONE | title={}", formatted["title"][:40])
        return {"success": True, "data": result}

    except Exception as e:
        logger.exception("[V2Pipeline] FAILED: {}", e)
        return {"success": False, "error": str(e)}
