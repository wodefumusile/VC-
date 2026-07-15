from __future__ import annotations
"""
登录状态检测  v2.2

纯检测函数，不做任何导航。返回详细状态供 login.py 决策。
"""

from loguru import logger
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from playwright.sync_api import Page  # type: ignore


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# 后台首页关键词 — 至少命中 2 个才判为已登录
ADMIN_KEYWORDS = ["新建群发", "素材管理", "数据统计", "用户管理", "首页"]
MIN_ADMIN_HITS = 2

# 登录页关键词（说明当前是登录 / 扫码态）
LOGIN_KEYWORDS = [
    "扫描二维码", "扫一扫", "请使用微信",
    "微信扫一扫", "关注公众号", "扫码登录",
]

# 登录过期/需重新登录 关键词（优先级最高）
EXPIRED_KEYWORDS = [
    "请重新登录", "重新登录", "登录过期",
    "会话过期", "请登录", "登录已超时",
]

# 二维码过期 / 超时 关键词
QR_TIMEOUT_KEYWORDS = [
    "登录超时", "登录已超时",
    "二维码已过期", "二维码过期",
    "重新获取", "点击刷新",
    "请刷新", "已失效",
]


# ---------------------------------------------------------------------------
def check_login(page: Page) -> dict:
    """检测登录状态（纯检测，不导航）

    返回 dict:
        logged_in  : bool
        reason     : str   "home_url" | "admin_text" | "expired_text"
                          | "qr_timeout" | "waiting_scan" | "unknown"
        detail     : str   额外信息
    """

    # 1 — URL 快速判断 —
    url = page.url
    if "/cgi-bin/home" in url:
        logger.success("已登录 (URL: home)")
        return {"logged_in": True, "reason": "home_url", "detail": url}

    # 2 — 获取页面文本 —
    try:
        all_text = page.locator("body").inner_text(timeout=2000)
    except Exception:
        all_text = ""

    # 3 — 优先检测"请重新登录"等过期文本（这些可能出现在后台页面上，优先判断）—
    for kw in EXPIRED_KEYWORDS:
        if kw in all_text:
            logger.warning("登录已过期: 检测到「{}」", kw)
            return {
                "logged_in": False,
                "reason": "expired_text",
                "detail": kw,
            }

    # 4 — 后台关键词检测 —
    hits = [kw for kw in ADMIN_KEYWORDS if kw in all_text]
    if len(hits) >= MIN_ADMIN_HITS:
        logger.success("已登录 (关键词: {})", hits)
        return {"logged_in": True, "reason": "admin_text", "detail": str(hits)}

    # 5 — 二维码过期 / 超时 —
    for kw in QR_TIMEOUT_KEYWORDS:
        if kw in all_text:
            logger.warning("二维码已过期/超时: 检测到「{}」", kw)
            return {
                "logged_in": False,
                "reason": "qr_timeout",
                "detail": kw,
            }

    # 6 — 登录页（二维码有效，等待扫码）—
    for kw in LOGIN_KEYWORDS:
        if kw in all_text:
            logger.debug("等待扫码中... (关键词: {})", kw)
            return {
                "logged_in": False,
                "reason": "waiting_scan",
                "detail": kw,
            }

    # 7 — 兜底 —
    snippet = all_text[:300].replace("\n", " ") if all_text else "<empty>"
    logger.warning("无法确定登录状态 | URL={}", url)
    logger.warning("页面文本预览: {}", snippet)
    return {"logged_in": False, "reason": "unknown", "detail": url}
