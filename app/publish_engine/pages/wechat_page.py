from __future__ import annotations
"""
微信公众号后台页面操作

Phase 2 仅验证登录后可进入后台。
"""

from loguru import logger
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from playwright.sync_api import Page  # type: ignore

from publish_engine.browser.config import WECHAT_MP_URL
from publish_engine.auth.session import check_login


def open_home(page: Page) -> dict:
    """打开微信公众号后台首页

    Returns:
        {"success": True/False, "url": "...", "message": "..."}
    """
    logger.info("打开微信公众号后台...")

    try:
        page.goto(WECHAT_MP_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)

        status = check_login(page)
        if status["logged_in"]:
            logger.success("已进入微信公众号后台: {}", page.url)
            return {
                "success": True,
                "url": page.url,
                "title": page.title(),
                "message": "成功进入后台首页",
            }

        logger.error("未登录，无法进入后台")
        return {"success": False, "url": page.url, "message": "未登录，请先扫码"}

    except Exception as e:
        logger.exception("打开后台失败")
        return {"success": False, "url": "", "message": str(e)}


def get_account_info(page: Page) -> dict:
    """获取公众号基本信息（登录后可用）"""
    try:
        page.goto(WECHAT_MP_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)

        name_el = page.locator(".account_name, .nickname, #nickname").first
        name = name_el.inner_text() if name_el.count() > 0 else "未知"

        return {"name": name, "url": page.url}
    except Exception:
        return {"name": "获取失败", "url": page.url if page else ""}
