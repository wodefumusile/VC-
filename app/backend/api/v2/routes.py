"""API v2 routes — v2.1.1 capabilities.

All v2 routes use /api/v2 prefix, keeping v1 /api/ unchanged.
"""

import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from loguru import logger

from backend.config import settings
from backend.utils.exceptions import success_response, error_response, ErrorCode, AppError
from backend.services.image_provider import get_image_provider
from backend.services.formatter_engine import format_article as v2_format_article
from backend.services.quality_checker_v2 import quality_checker_v2
from backend.services.workflow_v2_orchestrator import run_v2_pipeline

router = APIRouter(prefix="/api/v2", tags=["v2.1"])

# ===== Auth =====

security = HTTPBearer(auto_error=False)


def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> None:
    """Verify Bearer token matches ADMIN_TOKEN.

    Raises HTTPException(403) if not configured or token mismatch.
    """
    admin_token = settings.ADMIN_TOKEN
    if not admin_token:
        raise HTTPException(status_code=403, detail="ADMIN_TOKEN not configured on server")
    if not credentials or credentials.credentials != admin_token:
        raise HTTPException(status_code=403, detail="Invalid or missing admin token")


# ============ Image Generation ============

class ImageGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="图片生成 prompt")


@router.post("/image/generate", summary="🎨 图片生成")
async def generate_image(req: ImageGenerateRequest):
    """Generate image via configured IMAGE_PROVIDER."""
    provider = get_image_provider()
    result = provider.generate(req.prompt)
    if result.success:
        return success_response({
            "image_url": result.image_url,
            "task_id": result.task_id,
            "provider": result.provider,
        })
    raise AppError(ErrorCode.AI_API_ERROR, result.error, status_code=502)


# ============ Formatter ============

class FormatterRenderRequest(BaseModel):
    title: str = Field(..., min_length=1, description="文章标题")
    content: str = Field(..., min_length=1, description="正文（支持 Markdown/HTML/纯文本）")
    author: str = Field(default="", description="作者")
    template: str = Field(default="knowledge", description="模板: technology/business/knowledge/personal")


@router.post("/formatter/render", summary="🎹 高级排版渲染")
async def formatter_render(req: FormatterRenderRequest):
    """Render article with v2 FormatterEngine (section+span)."""
    result = v2_format_article(
        title=req.title,
        content=req.content,
        author=req.author,
        template=req.template,
    )
    return success_response(result)


# ============ Quality Check ============

class QualityCheckRequest(BaseModel):
    title: str = Field(..., min_length=1, description="文章标题")
    content_html: str = Field(..., min_length=1, description="HTML 正文")
    has_cover: bool = Field(default=False, description="是否有封面图")
    image_count: int = Field(default=0, description="插图数量")


@router.post("/quality/check", summary="✅ 质量检测 v2")
async def quality_check(req: QualityCheckRequest):
    """Enhanced quality check (covers content, images, HTML)."""
    images = []
    if req.has_cover:
        images.append({"type": "cover", "image_url": "placeholder", "status": "generated"})
    for i in range(req.image_count):
        images.append({"type": "illustration", "image_url": "placeholder", "status": "generated", "position": i + 1})

    result = quality_checker_v2.check(
        title=req.title,
        content_html=req.content_html,
        images=images if images else None,
    )
    return success_response(result)


# ============ V2 Pipeline ============

class V2PipelineRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200, description="写作主题")
    style: str = Field(default="marketing", description="风格: marketing/science/case_study/branding")
    length: str = Field(default="medium", description="长度: short/medium/long")
    author: str = Field(default="wgzxhhh", description="作者")
    template: str = Field(default="knowledge", description="排版模板: technology/business/knowledge/personal")


@router.post("/pipeline/run", summary="🚀 V2 全流程（生成+配图+排版+质检+发布）")
async def v2_pipeline_run(req: V2PipelineRequest):
    """Run complete v2.1 pipeline in one call."""
    logger.info("V2 pipeline request | topic={}", req.topic)
    result = await run_v2_pipeline(
        topic=req.topic,
        style=req.style,
        length=req.length,
        author=req.author,
        template=req.template,
    )
    if result["success"]:
        return success_response(result["data"])
    raise AppError(ErrorCode.AI_API_ERROR, result.get("error", "Pipeline failed"), status_code=502)


# ============ Article Detail (v2.1.1 new) ============

@router.get("/articles/{article_id}", summary="📄 查看文章详情")
async def get_article(article_id: str):
    """Get full article content by article ID."""
    from backend.database import get_db
    db = get_db()
    article = db.get_article(article_id)
    if not article:
        raise AppError(ErrorCode.NOT_FOUND, f"Article not found: {article_id}", status_code=404)

    images = db.get_images_by_article(article_id)

    return success_response({
        "id": article["id"],
        "task_id": article["task_id"],
        "title": article["title"],
        "summary": article["summary"],
        "content_html": article["content_html"],
        "seo_keywords": article["seo_keywords"],
        "style": article["style"],
        "status": article["status"],
        "quality_score": article["quality_score"],
        "created_at": article["created_at"],
        "images": [
            {
                "id": img["id"],
                "image_url": img.get("image_url", ""),
                "prompt": img["prompt"],
                "type": img["type"],
                "position": img["position"],
                "status": img["status"],
            }
            for img in images
        ],
    })


# ============ Knowledge Engine (v2.1) ============

class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="搜索关键词")
    top_k: int = Field(default=5, ge=1, le=20, description="返回条数")


@router.post("/knowledge/search", summary="🔍 知识库检索")
async def knowledge_search(req: KnowledgeSearchRequest):
    """Search personal knowledge base (Obsidian vault)."""
    if not settings.obsidian_enabled:
        raise AppError(ErrorCode.CONFIG_ERROR, "知识库未启用 (OBSIDIAN_PATH 未设置)", status_code=400)

    try:
        from backend.services.knowledge_engine import KeywordJaccardRetriever
        retriever = KeywordJaccardRetriever(settings.OBSIDIAN_PATH)
        results = retriever.search(req.query, top_k=req.top_k)
        return success_response({
            "query": req.query,
            "total": len(results),
            "results": [
                {
                    "title": r.title,
                    "content": r.content[:500],
                    "source": r.source,
                    "score": r.score,
                    "meta": r.meta,
                }
                for r in results
            ],
        })
    except Exception as e:
        raise AppError(ErrorCode.AI_API_ERROR, f"知识库检索失败: {e}", status_code=500)


@router.get("/knowledge/scan", summary="📊 知识库概览")
async def knowledge_scan():
    """Scan knowledge base overview (file count, categories, etc.)."""
    if not settings.obsidian_enabled:
        raise AppError(ErrorCode.CONFIG_ERROR, "知识库未启用 (OBSIDIAN_PATH 未设置)", status_code=400)

    try:
        from backend.services.knowledge_engine import KeywordJaccardRetriever
        retriever = KeywordJaccardRetriever(settings.OBSIDIAN_PATH)
        result = retriever.scan()
        return success_response({
            "total_files": result.total_files,
            "total_chars": result.total_chars,
            "categories": result.categories,
            "sample_titles": result.sample_titles[:10],
        })
    except Exception as e:
        raise AppError(ErrorCode.AI_API_ERROR, f"知识库扫描失败: {e}", status_code=500)


# ============ Config Management (v2.1.1 hardened) ============

class ConfigUpdateRequest(BaseModel):
    ai_api_key: str = Field(default="", description="AI API Key")
    image_api_key: str = Field(default="", description="图片生成 API Key")
    obsidian_path: str = Field(default="", description="Obsidian Vault 路径")
    enable_ai: bool = Field(default=True, description="启用 AI 生成")
    enable_knowledge: bool = Field(default=True, description="启用知识库")
    enable_image: bool = Field(default=True, description="启用图片生成")


@router.get("/config", summary="⚙️ 获取当前配置")
async def get_config():
    """Get current config (API keys fully masked)."""
    return success_response({
        "app_version": settings.APP_VERSION,
        "ai_api_key": _mask_key(settings.AI_API_KEY),
        "ai_model": settings.AI_MODEL,
        "image_provider": settings.IMAGE_PROVIDER,
        "image_api_key": _mask_key(settings.IMAGE_API_KEY),
        "obsidian_path": settings.OBSIDIAN_PATH,
        "enable_ai_generate": settings.ENABLE_AI_GENERATE,
        "enable_knowledge": settings.ENABLE_KNOWLEDGE,
        "enable_image": settings.ENABLE_IMAGE,
        "obsidian_enabled": settings.obsidian_enabled,
        "image_enabled": settings.image_enabled,
        "publish_mode": settings.PUBLISH_MODE,
    })


@router.post("/config", summary="⚙️ 更新配置（需 Admin Token）")
async def update_config(
    req: ConfigUpdateRequest,
    _auth=Depends(verify_admin),
):
    """Update .env config file. Requires Bearer ADMIN_TOKEN.

    - Skips masked keys (containing ****) to prevent accidental overwrites.
    - Hot-reloads settings so changes take effect immediately.
    """
    try:
        env_path: Path = settings.ROOT_DIR / ".env"

        # Backup before write
        backup_path = env_path.with_suffix(".env.backup")
        if env_path.exists():
            shutil.copy2(env_path, backup_path)
            logger.info("Config: backed up .env to .env.backup")

        # Read existing .env
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        updates = {}

        # Skip masked keys (frontend shows sk-1****0b2c, don't write that back)
        if req.ai_api_key and "****" not in req.ai_api_key:
            updates["AI_API_KEY"] = req.ai_api_key
        if req.image_api_key and "****" not in req.image_api_key:
            updates["IMAGE_API_KEY"] = req.image_api_key
        if req.obsidian_path:
            updates["OBSIDIAN_PATH"] = req.obsidian_path
        updates["ENABLE_AI_GENERATE"] = str(req.enable_ai).lower()
        updates["ENABLE_KNOWLEDGE"] = str(req.enable_knowledge).lower()
        updates["ENABLE_IMAGE"] = str(req.enable_image).lower()

        # Update matching lines
        new_lines = []
        updated_keys = set()
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                matched = False
                for key, val in updates.items():
                    if stripped.startswith(f"{key}="):
                        new_lines.append(f"{key}={val}\n")
                        updated_keys.add(key)
                        matched = True
                        break
                if not matched:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        # Append new keys
        for key, val in updates.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={val}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        # Hot-reload settings so changes take effect immediately
        if updated_keys:
            from backend.config.settings import reload_settings
            reload_settings()
            logger.info("Config hot-reloaded")

        logger.info("Config updated | keys={}", list(updated_keys))
        return success_response({
            "message": "配置已保存，已自动生效",
            "updated_keys": list(updated_keys),
        })

    except Exception as e:
        logger.exception("Config update failed")
        raise AppError(ErrorCode.CONFIG_ERROR, "配置更新失败，请检查日志", status_code=500)


# ============ Key Test (v2.1.1 new) ============

class TestAiKeyRequest(BaseModel):
    api_key: str = Field(..., min_length=1, description="要测试的 AI API Key")


@router.post("/config/test-ai-key", summary="🔑 测试 AI Key 连接")
async def test_ai_key(req: TestAiKeyRequest):
    """Test DeepSeek API key by making a minimal chat request."""
    from openai import OpenAI
    try:
        client = OpenAI(api_key=req.api_key, base_url="https://api.deepseek.com")
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
        )
        logger.info("AI Key test: success")
        return success_response({"status": "success", "message": "AI API Key 有效"})
    except Exception as e:
        error_msg = str(e)
        logger.warning("AI Key test failed: {}", error_msg[:200])
        raise AppError(ErrorCode.AI_API_ERROR, error_msg[:500], status_code=400)


class TestImageKeyRequest(BaseModel):
    api_key: str = Field(..., min_length=1, description="要测试的图片 API Key")


@router.post("/config/test-image-key", summary="🎨 测试图片 Key")
async def test_image_key(req: TestImageKeyRequest):
    """Test image generation API key."""
    import requests
    try:
        resp = requests.get(
            "https://ark.cn-beijing.volces.com/api/v3/models",
            headers={"Authorization": f"Bearer {req.api_key}"},
            timeout=10,
        )
        if resp.status_code == 200:
            logger.info("Image Key test: success")
            return success_response({"status": "success", "message": "图片 API Key 有效"})
        else:
            raise AppError(ErrorCode.AI_API_ERROR, f"HTTP {resp.status_code}: {resp.text[:200]}", status_code=400)
    except Exception as e:
        logger.warning("Image Key test failed: {}", str(e)[:200])
        raise AppError(ErrorCode.AI_API_ERROR, str(e)[:500], status_code=400)


def _mask_key(key: str) -> str:
    """Fully mask API key: sk-ab****234 for display."""
    if not key:
        return ""
    if len(key) <= 8:
        return key[:2] + "****" + key[-2:] if len(key) >= 4 else "****"
    return key[:4] + "****" + key[-4:]
