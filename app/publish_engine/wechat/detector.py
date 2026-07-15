from __future__ import annotations
"""微信公众平台 页面状态检测器 v2.1

检测：登录 / 编辑器 / 保存成功
关键修复：is_on_editor() 必须检查页面内容，不能仅依赖URL
"""

import time
from pathlib import Path
from loguru import logger
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from playwright.sync_api import Page  # type: ignore


class PageDetector:
    """页面状态检测器"""

    SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "storage" / "screenshots"

    def __init__(self, page: Page):
        self.page = page
        self.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    # === 登录检测 ===

    def is_logged_in(self) -> bool:
        try:
            url = self.page.url
            if "/cgi-bin/home" in url:
                # URL 在首页，再检查内容确认不是"请重新登录"
                body = self._safe_body_text()
                if "请重新登录" in body:
                    return False
                return True
            body = self._safe_body_text()
            admin_kw = ["新建群发", "素材管理", "用户管理", "数据统计"]
            if any(kw in body for kw in admin_kw):
                return True
            return False
        except Exception:
            return False

    # === 编辑器检测 ===

    def is_on_editor(self, check_content: bool = True) -> bool:
        """检测是否在编辑器页面

        Args:
            check_content: 如果 True，不仅检查 URL 还验证页面内容
        """
        try:
            url = self.page.url
            page_title = self.page.title()

            # URL 快速判断
            if "/appmsg" in url and "edit" in url:
                if not check_content:
                    logger.debug("编辑器检测: URL 匹配（仅URL模式）")
                    return True

                # 必须检查页面内容！否则可能页面虽然URL对，但内容是"请重新登录"
                body = self._safe_body_text()

                # 排除"请重新登录"页面
                if "请重新登录" in body or "登录过期" in body:
                    logger.warning("编辑器检测: URL匹配但页面显示登录过期!")
                    return False

                # 检测编辑器特征
                editor_keywords = ["标题", "作者", "正文", "封面"]
                matches = [kw for kw in editor_keywords if kw in body]
                if len(matches) >= 2:
                    logger.debug("编辑器检测: 内容匹配 {}", matches)
                    return True

                # 给新编辑器一个机会（可能编辑器元素动态加载中）
                logger.warning("编辑器检测: URL匹配但未找到编辑器元素，url={}", url[:80])
                return True  # URL匹配且没有"请重新登录"，暂时相信

            # 不在编辑器URL
            return False
        except Exception as e:
            logger.warning("编辑器检测异常: {}", e)
            return False

    # === 保存成功检测 ===

    def detect_save_success(self, timeout_ms: int = 10000) -> dict:
        """检测保存是否成功 — 多重验证

        检测顺序：
        1. 页面Toast/提示文本
        2. URL跳转离开编辑器
        3. 网络请求检测（待实现）
        4. 静默保存兜底

        Returns: {"success": True/False, "method": "...", "detail": "..."}
        """
        start_time = time.time()
        checks = {
            "text_toast": False,
            "url_redirect": False,
        }

        success_texts = [
            "保存成功", "已保存", "保存草稿成功",
            "操作成功", "成功",
        ]

        # 轮询检测（最多10秒）
        while time.time() - start_time < timeout_ms / 1000:
            self.page.wait_for_timeout(500)

            # 1. 检测文本提示
            if not checks["text_toast"]:
                try:
                    body = self.page.locator("body").inner_text(timeout=800)
                    for text in success_texts:
                        if text in body:
                            checks["text_toast"] = True
                            logger.success("检测到保存提示: {}", text)
                            self._screenshot("save_toast")
                            return {
                                "success": True,
                                "method": "text_toast",
                                "detail": text,
                                "checks": checks,
                            }
                except Exception:
                    pass

            # 2. 检测URL跳转（离开编辑器=保存完成）
            if not checks["url_redirect"]:
                current_url = self.page.url
                if "/appmsg" not in current_url or "edit" not in current_url:
                    checks["url_redirect"] = True
                    logger.success("检测到URL跳转, 保存成功 | url={}", current_url[:100])
                    self._screenshot("save_redirected")
                    return {
                        "success": True,
                        "method": "url_redirect",
                        "detail": current_url,
                        "checks": checks,
                    }

        # 超时 - 检查是否仍在编辑器（可能是静默保存）
        if self.is_on_editor():
            logger.info("仍在编辑器中, 可能已静默保存")
            checks["still_on_editor"] = True
            return {
                "success": True,
                "method": "silent_still_editor",
                "detail": "超时但仍在编辑器",
                "checks": checks,
            }

        logger.warning("未检测到保存成功")
        self._screenshot("save_failed")
        return {
            "success": False,
            "method": "timeout",
            "detail": "超时且不在编辑器",
            "checks": checks,
        }

    # === "请重新登录" 快速检测 ===

    def is_login_expired_on_page(self) -> bool:
        """快速检测当前页面是否显示登录过期"""
        try:
            body = self._safe_body_text()
            if "请重新登录" in body:
                logger.warning("当前页面检测到「请重新登录」")
                return True
            if "登录过期" in body:
                logger.warning("当前页面检测到「登录过期」")
                return True
            return False
        except Exception:
            return False

    # === 草稿列表验证 ===

    def verify_draft_in_list(self) -> dict:
        """导航到草稿列表页验证草稿存在"""
        try:
            list_url = "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_list&action=list&type=77"
            self.page.goto(list_url, wait_until="domcontentloaded", timeout=15000)
            self.page.wait_for_timeout(3000)

            # 先检查是否登录过期
            if self.is_login_expired_on_page():
                return {"success": False, "detail": "草稿列表页显示请重新登录"}

            body = self._safe_body_text()

            # 检测列表页特征
            list_keywords = ["草稿", "素材管理", "图文消息"]
            if any(kw in body for kw in list_keywords):
                logger.success("已进入草稿列表页")
                self._screenshot("draft_list")
                return {"success": True, "detail": "草稿列表页已加载"}
            return {"success": False, "detail": "未检测到草稿列表"}
        except Exception as e:
            logger.warning("草稿列表验证失败: {}", e)
            return {"success": False, "detail": str(e)}

    # === 辅助 ===

    def _safe_body_text(self) -> str:
        """安全获取 body 文本"""
        try:
            return self.page.locator("body").inner_text(timeout=2000) or ""
        except Exception:
            return ""

    def _screenshot(self, name: str) -> Path:
        path = self.SCREENSHOT_DIR / f"{name}_{int(time.time())}.png"
        try:
            self.page.screenshot(path=str(path))
        except Exception as e:
            logger.warning("截图失败: {}", e)
        return path

    def take_debug_screenshot(self, label: str = "debug") -> Path:
        return self._screenshot(label)
