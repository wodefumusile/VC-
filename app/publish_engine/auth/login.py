from __future__ import annotations
"""
微信公众号登录流程  v2.5

使用 page.wait_for_url() 等待扫码后的自动跳转，不干扰页面。
登录成功后自动提取并保存 token + auth_state。
"""

import time
import re
from loguru import logger
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from playwright.sync_api import Page  # type: ignore

from publish_engine.browser.config import WECHAT_MP_URL, LOGIN_TIMEOUT, set_token, get_token
from publish_engine.auth.session import check_login
from publish_engine.browser.browser_manager import browser_manager


MAX_QR_WAIT = 300  # 5分钟


def extract_token_from_url(url: str) -> str | None:
    """从微信后台 URL 中提取 token 参数"""
    match = re.search(r'token=(\d+)', url)
    return match.group(1) if match else None


def start_login(page: Page, timeout: int = MAX_QR_WAIT) -> dict:
    """登录流程

    1. 打开公众号后台
    2. 已登录 → 提取token + 保存 auth_state + 直接返回
    3. 未登录 → 等待扫码
    4. 扫码成功 → 提取token + 保存 auth_state
    """

    logger.info("=" * 50)
    logger.info("登录流程启动 | 最大等待 {}s", timeout)
    logger.info("=" * 50)

    # ── 1. 打开公众号后台 ──
    logger.info("打开 {}", WECHAT_MP_URL)
    try:
        page.goto(WECHAT_MP_URL, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        logger.warning("加载异常: {}", e)

    page.wait_for_timeout(3000)

    # ── 2. 检查是否已登录 ──
    status = check_login(page)
    if status["logged_in"]:
        logger.success("已登录 | {}", status.get("reason"))
        # 提取 token
        token = extract_token_from_url(page.url)
        if token:
            set_token(token)
            logger.success("提取到 token: {}", token)
        else:
            logger.warning("未找到 token，URL: {}", page.url)
        # 保存登录态
        browser_manager.save_auth()
        return {"success": True, "message": "已登录", "need_scan": False, "token": token}

    # ── 3. 检查是否是"请重新登录" ──
    if status.get("reason") == "expired_text":
        logger.warning("检测到登录已过期: {}", status.get("detail"))
        logger.info("请在浏览器中重新扫码...")

    # ── 4. 未登录，等待扫码 ──
    logger.info("")
    logger.info("扫码登录二维码已显示在浏览器中")
    logger.info("请用微信扫描，扫码后页面会自动跳转")
    logger.info("等待时间上限: {} 秒", timeout)
    logger.info("")

    try:
        page.wait_for_url(
            "**/cgi-bin/home*",
            timeout=timeout * 1000,
            wait_until="domcontentloaded",
        )
        logger.success("扫码成功！已进入后台首页")
        page.wait_for_timeout(1500)

        # 提取 token
        token = extract_token_from_url(page.url)
        if token:
            set_token(token)
            logger.success("提取到 token: {}", token)
        else:
            logger.warning("未找到 token")

        # 保存登录态
        browser_manager.save_auth()

        return {"success": True, "message": "登录成功", "need_scan": False, "token": token}

    except Exception:
        final_url = page.url
        logger.warning("等待超时 | 当前URL: {}", final_url)

        # 再检查一次
        status = check_login(page)
        if status["logged_in"]:
            logger.success("最终检测: 已登录")
            token = extract_token_from_url(page.url)
            if token:
                set_token(token)
            browser_manager.save_auth()
            return {"success": True, "message": "登录成功", "need_scan": False, "token": token}

        logger.error("登录超时，未检测到扫码")
        return {
            "success": False,
            "message": f"等待 {timeout}s 后仍未登录",
            "need_scan": True,
        }
