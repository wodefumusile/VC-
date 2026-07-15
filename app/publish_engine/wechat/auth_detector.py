from __future__ import annotations
"""
编辑器前置登录守卫  v2.2

在进入编辑器之前，强制验证登录态。
使用 token 参数确保不被踢回登录页。
"""

import time
from pathlib import Path
from loguru import logger
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from playwright.sync_api import Page  # type: ignore

from publish_engine.auth.session import check_login
from publish_engine.browser.browser_manager import browser_manager
from publish_engine.browser.config import get_home_url, get_token

MP_MAIN = "https://mp.weixin.qq.com"


class AuthGuard:
    """登录守卫 — 所有编辑器操作前调用"""

    SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "storage" / "screenshots"

    def __init__(self, page: Page):
        self.page = page
        self.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        self.login_checked_at = 0
        self.session_status = "unknown"

    def verify_login(self) -> dict:
        """验证当前登录态是否有效

        使用带 token 的首页 URL 进行检测，避免被踢回登录页。

        Returns:
            {"logged_in": True/False, "reason": "...", "recovered": bool}
        """
        logger.info("=" * 40)
        logger.info("登录守卫: 验证登录态...")

        # 使用带 token 的首页 URL
        home_url = get_home_url()
        logger.info("导航到首页: {}", home_url[:80])

        try:
            self.page.goto(home_url, wait_until="domcontentloaded", timeout=20000)
        except Exception:
            try:
                self.page.wait_for_timeout(3000)
            except Exception:
                pass

        try:
            self.page.wait_for_timeout(2000)
        except Exception:
            pass

        # 检测
        status = check_login(self.page)

        if status["logged_in"]:
            self.session_status = "valid"
            self.login_checked_at = time.time()
            logger.success("登录守卫: ✅ 登录有效 | {}", status.get("reason"))
            return {"logged_in": True, "reason": status.get("reason"), "recovered": False}

        # ── 登录失效 ──
        self.session_status = "expired"
        reason = status.get("reason", "unknown")
        detail = status.get("detail", "")
        logger.warning("登录守卫: ❌ 登录失效 | reason={} | detail={}", reason, detail)
        self._screenshot("auth_expired")

        if reason == "expired_text":
            return self._recover_by_scan()

        if reason == "qr_timeout":
            logger.info("二维码已过期，刷新页面...")
            try:
                self.page.goto(MP_MAIN, wait_until="domcontentloaded", timeout=20000)
                self.page.wait_for_timeout(3000)
            except Exception:
                pass
            return self._recover_by_scan()

        return self._recover_by_scan()

    def _recover_by_scan(self) -> dict:
        """打开登录页，等待用户扫码"""
        logger.info("登录守卫: 正在打开登录页...")
        try:
            self.page.goto(MP_MAIN, wait_until="domcontentloaded", timeout=20000)
            self.page.wait_for_timeout(3000)
        except Exception:
            pass

        status = check_login(self.page)
        if status["logged_in"]:
            self.session_status = "valid"
            self.login_checked_at = time.time()
            browser_manager.save_auth()
            logger.success("登录守卫: ✅ 自动恢复成功")
            return {"logged_in": True, "reason": "auto_recovered", "recovered": True}

        logger.info("=" * 40)
        logger.info("请在浏览器中扫描微信二维码")
        logger.info("等待时间: 最多 5 分钟")
        logger.info("=" * 40)

        try:
            self.page.wait_for_url(
                "**/cgi-bin/home*",
                timeout=300000,
                wait_until="domcontentloaded",
            )
            self.session_status = "valid"
            self.login_checked_at = time.time()
            # 提取并保存 token
            from publish_engine.browser.config import set_token
            import re
            token_match = re.search(r'token=(\d+)', self.page.url)
            if token_match:
                set_token(token_match.group(1))
            browser_manager.save_auth()
            logger.success("登录守卫: ✅ 扫码恢复成功！")
            self._screenshot("auth_recovered")
            return {"logged_in": True, "reason": "scan_recovered", "recovered": True}
        except Exception:
            logger.error("登录守卫: ❌ 扫码超时")
            self._screenshot("auth_timeout")
            return {"logged_in": False, "reason": "scan_timeout", "recovered": False}

    def verify_login_on_page(self) -> dict:
        """在当前页面检测登录态（不导航）"""
        status = check_login(self.page)
        if status["logged_in"]:
            return {"logged_in": True, "reason": status.get("reason")}
        if status.get("reason") == "expired_text":
            logger.warning("当前页面检测到: {}", status.get("detail"))
            self._screenshot("login_expired_on_page")
            return {"logged_in": False, "reason": "expired_text", "detail": status.get("detail")}
        return {"logged_in": False, "reason": status.get("reason", "not_on_home")}

    def is_session_valid(self) -> bool:
        return self.session_status == "valid"

    def log_health(self):
        logger.info("Session健康: status={} | last_check={}s ago | token={}",
                     self.session_status,
                     int(time.time() - self.login_checked_at) if self.login_checked_at else "N/A",
                     get_token())

    def _screenshot(self, name: str) -> Path:
        path = self.SCREENSHOT_DIR / f"{name}_{int(time.time())}.png"
        try:
            self.page.screenshot(path=str(path))
        except Exception:
            pass
        return path
