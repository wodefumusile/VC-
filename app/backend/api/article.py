"""文章生成接口 + 内容分析"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from loguru import logger

from backend.utils.exceptions import success_response, error_response, ErrorCode, AppError
from backend.services.ai import article_generator
from backend.services.content_optimizer import seo_optimizer, quality_checker, compliance_checker
from backend.services.content_analyzer import auto_parse_wechat, auto_parse_douyin, analyze_topic, generate_article_from_analysis
from backend.database import get_db, TaskStatus

router = APIRouter(prefix="/api/article", tags=["📝 文章生成"])


class ArticleGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200, description="文章主题（必填）")
    style: str = Field(default="marketing", description="风格")
    length: str = Field(default="medium", description="长度")
    author: str = Field(default="wgzxhhh", description="作者")
    template: str = Field(default="knowledge", description="排版模板: business/knowledge/marketing/personal")
class SourceGenerateRequest(BaseModel):
    wechat_url: str = Field(default="", description="公众号链接")
    douyin_url: str = Field(default="", description="抖音链接")
    style: str = Field(default="marketing", description="风格")
    length: str = Field(default="medium", description="长度")
    author: str = Field(default="wgzxhhh", description="作者")
    template: str = Field(default="knowledge", description="排版模板")
class SEORequest(BaseModel):
    title: str = Field(..., min_length=1, description="文章标题")
    content_html: str = Field(..., min_length=1, description="HTML正文内容")
    seo_keywords: str = Field(default="", description="已有关键词")

class CheckRequest(BaseModel):
    title: str = Field(..., min_length=1, description="文章标题")
    content_html: str = Field(..., min_length=1, description="HTML正文内容")


# ============ 内容分析 ============

@router.post("/analyze", summary="🔍 分析链接内容", description="分析公众号/抖音链接，返回选题建议")
async def analyze_content(req: SourceGenerateRequest):
    """分析公众号/抖音链接内容，返回选题建议"""
    if not req.wechat_url and not req.douyin_url:
        raise AppError(ErrorCode.VALIDATION_ERROR, "请至少输入一个公众号链接或抖音链接")

    wechat_data = None
    douyin_data = None

    if req.wechat_url:
        logger.info("解析公众号链接: {}", req.wechat_url[:60])
        wechat_data = auto_parse_wechat(req.wechat_url)
        if not wechat_data:
            raise AppError(ErrorCode.VALIDATION_ERROR, "无法解析该公众号文章，请检查链接是否正确")

    if req.douyin_url:
        logger.info("解析抖音链接: {}", req.douyin_url[:60])
        douyin_data = auto_parse_douyin(req.douyin_url)

    analysis = analyze_topic(wechat_data=wechat_data, douyin_data=douyin_data)

    return success_response({
        "wechat_data": wechat_data,
        "douyin_data": douyin_data,
        "analysis": analysis,
    })


@router.post("/generate_from_source", summary="🎯 基于链接生成文章", description="分析链接内容 → AI选题 → 生成文章")
async def generate_from_source(req: SourceGenerateRequest):
    """完整流程：解析链接 → 选题分析 → 生成文章"""
    if not req.wechat_url and not req.douyin_url:
        raise AppError(ErrorCode.VALIDATION_ERROR, "请至少输入一个公众号链接或抖音链接")

    wechat_data = None
    douyin_data = None

    if req.wechat_url:
        wechat_data = auto_parse_wechat(req.wechat_url)
        if not wechat_data:
            raise AppError(ErrorCode.VALIDATION_ERROR, "无法解析该公众号文章")

    if req.douyin_url:
        douyin_data = auto_parse_douyin(req.douyin_url)

    analysis = analyze_topic(wechat_data=wechat_data, douyin_data=douyin_data)

    if analysis.get("error"):
        raise AppError(ErrorCode.AI_API_ERROR, analysis["error"])

    try:
        article = generate_article_from_analysis(analysis, style=req.style, length=req.length)
    except RuntimeError as e:
        raise AppError(ErrorCode.AI_API_ERROR, str(e), status_code=502) from e

    result = {
        "title": article["title"],
        "author": req.author,
        "summary": article["summary"],
        "content_html": article["content_html"],
        "seo_keywords": article["seo_keywords"],
        "style": article["style"],
        "analysis": analysis,
        "source": {
            "wechat_url": req.wechat_url,
            "douyin_url": req.douyin_url,
        }
    }

    db = get_db()
    task = db.create_article(
        topic=analysis.get("core_topic", req.wechat_url or req.douyin_url),
        style=req.style,
        title=article["title"],
        summary=article["summary"],
        content_html=article["content_html"],
        seo_keywords=article["seo_keywords"],
    )
    return success_response({**result, "task_id": task["task_id"]})


# ============ 原有接口 ============

@router.post("/generate", summary="✏️ AI生成文章", description="输入主题，AI自动写一篇公众号文章")
async def generate_article(req: ArticleGenerateRequest):
    logger.info("Generate article request, topic={} style={} length={}", req.topic, req.style, req.length)
    available = article_generator.get_available_styles()
    if req.style not in available:
        raise AppError(ErrorCode.VALIDATION_ERROR, "不支持的风格：" + req.style)
    try:
        article = article_generator.generate(topic=req.topic, style=req.style, length=req.length)
    except RuntimeError as e:
        logger.error("AI generation failed: {}", e)
        raise AppError(ErrorCode.AI_API_ERROR, str(e), status_code=502) from e

    from pydantic import BaseModel
    class AR(BaseModel):
        title: str; author: str; summary: str; content_html: str; seo_keywords: str; style: str

    result = AR(
        title=article["title"], author=req.author, summary=article["summary"],
        content_html=article["content_html"], seo_keywords=article["seo_keywords"], style=article["style"],
    )

    db = get_db()
    task = db.create_article(
        topic=req.topic, style=req.style, title=article["title"],
        summary=article["summary"], content_html=article["content_html"], seo_keywords=article["seo_keywords"],
    )
    return success_response({**result.model_dump(), "task_id": task["task_id"]})


@router.post("/seo", summary="🔍 SEO优化", description="对已有文章进行SEO标题和关键词优化")
async def optimize_seo(req: SEORequest):
    logger.info("SEO optimize request, title_len={} html_len={}", len(req.title), len(req.content_html))
    result = seo_optimizer.optimize(req.title, req.content_html, req.seo_keywords)
    return success_response(result)


@router.post("/check", summary="✅ 质量检测", description="检测文章质量和合规性")
async def check_article(req: CheckRequest):
    logger.info("Quality check request, title_len={} html_len={}", len(req.title), len(req.content_html))
    quality = quality_checker.check(req.title, req.content_html)
    compliance = compliance_checker.check(req.title, req.content_html)
    return success_response({"quality": quality, "compliance": compliance})


@router.get("/styles", summary="📋 可用风格列表")
async def get_styles():
    return success_response({
        "styles": [
            {"id": "marketing", "name": "营销推广", "description": "吸引眼球的营销内容"},
            {"id": "science", "name": "科普知识", "description": "通俗易懂的科普内容"},
            {"id": "case_study", "name": "案例分析", "description": "深度案例解读"},
            {"id": "branding", "name": "品牌故事", "description": "有温度的品牌叙事"},
        ]
    })


# ============ 排版模板 ============

@router.get("/templates", summary="🎨 排版模板列表")
async def get_templates():
    """返回所有可用排版模板"""
    from backend.services.content_formatter import get_all_templates
    return success_response({"templates": get_all_templates()})


@router.get("/preview", summary="👁️ 排版预览")
async def preview_article(
    title: str = "预览标题",
    content: str = "预览内容",
    template: str = "knowledge"
):
    """预览排版效果（不保存）"""
    from backend.services.content_formatter import format_article
    result = format_article(title, content, "", template)
    return success_response({
        "preview_html": result["content_html"],
        "template": result["template"],
    })
