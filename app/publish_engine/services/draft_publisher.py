from __future__ import annotations
"""
草稿上传服务 - 基于 wechat 模块

通过 Playwright 将文章上传到微信公众号草稿箱。
"""

from loguru import logger
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from playwright.sync_api import Page  # type: ignore

from publish_engine.wechat import WechatEditor, WechatArticle


def upload_to_draft(page: Page, article_data: dict) -> dict:
    """上传文章到微信公众号草稿箱

    Args:
        page: Playwright Page 实例（已登录）
        article_data: {"title": str, "content": str, "summary": str}

    Returns:
        {"success": bool, "message": str, "screenshot": str | None}
    """
    article = WechatArticle(
        title=article_data.get("title", ""),
        content=article_data.get("content", ""),
        summary=article_data.get("summary", ""),
    )

    valid, err = article.validate()
    if not valid:
        return {"success": False, "message": f"文章数据校验失败: {err}"}

    editor = WechatEditor(page)
    return editor.publish_draft(article)
