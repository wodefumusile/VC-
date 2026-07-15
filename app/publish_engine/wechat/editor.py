"""WeChat editor interaction v3.0 - strict title validation"""

import time, re
from pathlib import Path
from loguru import logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

from .selectors import EditorSelectors
from .detector import PageDetector
from .article import WechatArticle
from .auth_detector import AuthGuard
from publish_engine.browser.config import get_editor_url, get_token

MATERIAL_LIST_URL = "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_list&action=list&type=77"
TITLE_MAX_LEN = 64  # WeChat strict limit


class WechatEditor:
    SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "storage" / "screenshots"

    def __init__(self, page: "Page"):
        self.page = page
        self.selectors = EditorSelectors(page)
        self.detector = PageDetector(page)
        self.guard = AuthGuard(page)
        self.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        self._editor_frame = None

    def open_editor(self) -> bool:
        logger.info("=" * 40)
        logger.info("Navigating to editor...")

        auth = self.guard.verify_login()
        if not auth["logged_in"]:
            logger.error("Login failed, cannot recover")
            return False
        if auth.get("recovered"):
            logger.info("Login recovered, continuing")
        self.guard.log_health()

        token = get_token()
        logger.info("Using token: {}", str(token)[:20] if token else "NONE")

        # Strategy 1: Try direct editor URL first
        editor_url = get_editor_url()
        logger.info("Trying direct editor URL: {}", editor_url[:100])
        self.page.goto(editor_url, wait_until="domcontentloaded", timeout=30000)
        self.page.wait_for_timeout(6000)
        self._screenshot("editor_direct")

        if self._check_editor_ready():
            logger.success("Entered editor (direct URL)")
            return True

        # Strategy 2: Navigate via draft list -> click "new"
        logger.info("Direct URL failed, trying draft list -> new...")
        list_url = f"{MATERIAL_LIST_URL}&token={token}&lang=zh_CN" if token else MATERIAL_LIST_URL
        self.page.goto(list_url, wait_until="domcontentloaded", timeout=30000)
        self.page.wait_for_timeout(4000)
        self._screenshot("draft_list")

        new_clicked = False
        new_selectors = [
            'text=新建图文消息',
            'a:has-text("新建")',
            'button:has-text("新建")',
            '[class*="create"]',
            '.weui-desktop-btn_primary',
        ]
        for sel in new_selectors:
            try:
                el = self.page.locator(sel).first
                if el.count() > 0:
                    el.click()
                    logger.info("Clicked new via: {}", sel)
                    new_clicked = True
                    break
            except Exception:
                continue

        if new_clicked:
            self.page.wait_for_timeout(6000)
            self._screenshot("editor_via_list")
            if self._check_editor_ready():
                logger.success("Entered editor (via draft list)")
                return True

        # Strategy 3: Use JS to find and click new button
        logger.info("Trying JS click...")
        try:
            self.page.evaluate("""
                () => {
                    const btns = document.querySelectorAll('a, button, span');
                    for (const b of btns) {
                        if (b.textContent.includes('新建')) {
                            b.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            self.page.wait_for_timeout(6000)
            if self._check_editor_ready():
                logger.success("Entered editor (JS click)")
                return True
        except Exception:
            pass

        body = self._safe_body_text()
        logger.error("Cannot enter editor! URL={} | body={}", self.page.url[:100], body[:200])
        self._screenshot("editor_failed")
        return False

    def _check_editor_ready(self) -> bool:
        if self.detector.is_login_expired_on_page():
            logger.error("Editor page shows login expired!")
            self._screenshot("editor_login_expired")
            return False
        if self.detector.is_on_editor(check_content=True):
            self._detect_editor_frame()
            self._screenshot("editor_opened")
            return True
        if "/cgi-bin/home" in self.page.url:
            logger.warning("Redirected to home page!")
            return False
        if "/appmsg" in self.page.url and "edit" in self.page.url:
            return True
        return False

    def _detect_editor_frame(self):
        for frame in self.page.frames:
            try:
                if "ueditor" in frame.url or "editor" in frame.url:
                    self._editor_frame = frame
                    logger.info("Found editor frame: {}", frame.url[:80])
                    return
            except Exception:
                pass
        self._editor_frame = None

    # ===== Fill entry points =====

    def fill_article(self, article: WechatArticle) -> bool:
        # CRITICAL: enforce WeChat 64-char title limit
        title = article.title
        if len(title) > TITLE_MAX_LEN:
            logger.warning("Title truncated from {} to {} chars", len(title), TITLE_MAX_LEN)
            title = title[:TITLE_MAX_LEN].rstrip()

        # Detect title/content swap
        if "<" in title and ">" in title:
            logger.error("TITLE HAS HTML TAGS - content/title swapped!")
            self._screenshot("title_has_html")
            return False
        if len(title) > TITLE_MAX_LEN * 2:
            logger.error("Title too long even after truncation: {} chars", len(title))
            return False

        logger.info("=" * 60)
        logger.info("======== WeChat Publish Data Validation ========")
        logger.info("Title ({} chars): {}", len(title), title[:80])
        logger.info("Author: {}", article.author)
        logger.info("Content length: {} chars", len(article.content))
        logger.info("Summary length: {} chars", len(article.summary or ""))
        logger.info("==================================")

        # Fill title first - most critical
        ok_title = self._fill_title(title)
        if not ok_title:
            logger.error("TITLE FILL FAILED - aborting fill!")
            self._screenshot("title_fill_failed")
            return False

        # Verify title was filled correctly
        self.page.wait_for_timeout(500)
        actual_title = self._get_title_text()
        if actual_title and len(actual_title) > len(title) * 3:
            logger.error("TITLE VERIFICATION FAILED: filled {} chars, expected {} chars. Content in title?",
                        len(actual_title), len(title))
            self._screenshot("title_content_swap")
            return False
        logger.info("Title verified: {} chars filled", len(actual_title or ""))

        self._fill_author(article.author)
        self._fill_content(article.content)
        self._fill_summary(article.summary or "")

        self._screenshot("article_filled")
        return True

    def _get_title_text(self) -> str:
        """Get current title text from editor for verification."""
        try:
            return self.page.evaluate("""
                () => {
                    const t = document.querySelector('#title');
                    if (t) return t.textContent || '';
                    const ta = document.querySelector('textarea#title');
                    if (ta) return ta.value || '';
                    return '';
                }
            """) or ""
        except Exception:
            return ""

    # ===== Title fill (v3.0 - multi-strategy with verification) =====

    def _fill_title(self, title: str) -> bool:
        logger.info("Filling title: {} chars", len(title))
        try:
            ok = self.page.evaluate("(t) => { var ta = document.querySelector('textarea#title'); if (ta) { var nativeSetter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set; nativeSetter.call(ta, t); ta.dispatchEvent(new Event('input', {bubbles: true})); ta.dispatchEvent(new Event('change', {bubbles: true})); var reactSetter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value'); reactSetter.set.call(ta, t); var ev = new Event('input', {bubbles: true}); Object.defineProperty(ev, 'target', {writable: false, value: ta}); ta.dispatchEvent(ev); return ta.value.length > 0; } return false; }", title)
            if ok:
                logger.success("Title JS OK")
                self.page.wait_for_timeout(300)
                return True
        except Exception as e:
            logger.warning("Title JS err: {}", e)
        try:
            ta = self.page.locator("textarea#title")
            if ta.count() > 0:
                ta.first.evaluate("el => { el.style.display = 'block'; }")
                self.page.wait_for_timeout(200)
                ta.first.click(timeout=3000, force=True)
                self.page.keyboard.press("Control+a")
                self.page.keyboard.press("Delete")
                self.page.keyboard.type(title, delay=20)
                self.page.wait_for_timeout(300)
                logger.success("Title force OK")
                return True
        except Exception as e:
            logger.warning("Title force err: {}", e)
        try:
            el = self.page.locator("#title")
            if el.count() > 0:
                el.first.click(timeout=5000, force=True)
                self.page.wait_for_timeout(500)
                self.page.keyboard.press("Control+a")
                self.page.keyboard.press("Delete")
                self.page.keyboard.type(title, delay=20)
                self.page.wait_for_timeout(500)
                logger.success("Title #title OK")
                return True
        except Exception as e:
            logger.warning("Title #title err: {}", e)
        logger.error("TITLE FAILED")
        return False
    # ===== Author fill =====

    def _fill_author(self, author: str) -> bool:
        if not author:
            return True
        logger.info("--- Filling author: {} ---", author)
        for sel in ["[placeholder*='作者']", "#author", "input[name='author']"]:
            try:
                el = self.page.locator(sel)
                if el.count() > 0:
                    el.first.click()
                    el.first.fill(author)
                    logger.success("Author filled ({})", sel)
                    return True
            except Exception:
                continue
        try:
            self.selectors.click_author_area()
            el = self.selectors.find_author_input()
            if el:
                el.fill(author)
                logger.success("Author filled (selectors)")
                return True
        except Exception:
            pass
        logger.warning("Author not found, skipping")
        return True  # Non-critical

    # ===== Content fill =====

    def _fill_content(self, content: str) -> bool:
        logger.info("--- Filling content ---")
        logger.info("Content length: {} chars", len(content))
        logger.info("Content preview: {}", content[:120])

        # Strategy 1: Direct ProseMirror injection
        try:
            result = self.page.evaluate("""
                (htmlContent) => {
                    const pms = document.querySelectorAll('.ProseMirror');
                    for (let pm of pms) {
                        if (!pm.closest('[id*="title"]')) {
                            pm.innerHTML = htmlContent;
                            return 'ok|len=' + pm.innerHTML.length;
                        }
                    }
                    return null;
                }
            """, content)
            if result:
                logger.success("Content injected (ProseMirror direct): {}", result)
                return True
        except Exception as e:
            logger.warning("ProseMirror injection failed: {}", e)

        # Strategy 2: Clipboard paste
        try:
            clip = self.page.evaluate("""
                (htmlContent) => {
                    const si = document.createElement('span');
                    si.innerHTML = htmlContent;
                    const blob = new Blob([si.innerHTML], {type: 'text/html'});
                    const data = [new ClipboardItem({'text/html': blob})];
                    return navigator.clipboard.write(data).then(() => 'ok').catch(e => 'err: ' + e);
                }
            """, content)
            logger.info("Clipboard write: {}", clip)
            self.page.wait_for_timeout(500)

            # Click body ProseMirror and paste
            self.page.evaluate("""
                () => {
                    const pms = document.querySelectorAll('.ProseMirror');
                    for (let pm of pms) {
                        if (!pm.closest('[id*="title"]')) {
                            pm.click();
                            pm.focus();
                            break;
                        }
                    }
                }
            """)
            self.page.wait_for_timeout(300)
            self.page.keyboard.press("Control+v")
            self.page.wait_for_timeout(1500)
            check = self.page.evaluate("""
                () => {
                    const pms = document.querySelectorAll('.ProseMirror');
                    for (let pm of pms) {
                        if (!pm.closest('[id*="title"]') && pm.textContent.length > 10) {
                            return 'clipboard|len=' + pm.textContent.length;
                        }
                    }
                    return null;
                }
            """)
            if check:
                logger.success("Content pasted ({})", check)
                return True
        except Exception as e:
            logger.warning("Clipboard paste failed: {}", e)

        # Strategy 3: selectors fallback
        if self.selectors.inject_content_html(content):
            self.page.wait_for_timeout(1500)
            logger.success("Content injected (selectors fallback)")
            return True

        logger.error("Content injection completely failed")
        return False

    # ===== Summary fill =====

    def _fill_summary(self, summary: str) -> bool:
        if not summary:
            return True
        logger.info("--- Filling summary ---")
        for sel in ["[placeholder*='摘要']", "textarea[name='summary']", "#summary"]:
            try:
                el = self.page.locator(sel)
                if el.count() > 0:
                    el.first.click()
                    el.first.fill(summary)
                    logger.success("Summary filled ({})", sel)
                    return True
            except Exception:
                continue
        try:
            self.selectors.click_summary_area()
            el = self.selectors.find_summary_input()
            if el:
                el.fill(summary)
                logger.success("Summary filled (selectors)")
                return True
        except Exception:
            pass
        logger.warning("Summary not found, skipping")
        return True

    # ===== Save draft =====

    def save_draft(self) -> dict:
        logger.info("Saving draft...")
        save_btn = self.selectors.find_save_button()
        if save_btn:
            try:
                save_btn.click()
                logger.info("Clicked save button")
                self.page.wait_for_timeout(2000)
                result = self.detector.detect_save_success()
                if result["success"]:
                    return result
            except Exception:
                pass

        logger.info("Using Ctrl+S ...")
        self.page.keyboard.press("Control+s")
        self.page.wait_for_timeout(2000)
        result = self.detector.detect_save_success()
        if result["success"]:
            return result

        # Try clicking save text
        try:
            save_link = self.page.get_by_text("保存", exact=False)
            if save_link.count() > 0:
                save_link.first.click()
                self.page.wait_for_timeout(2000)
                result = self.detector.detect_save_success()
                if result["success"]:
                    return result
        except Exception:
            pass

        # Last resort: check if page URL changed (draft saved = URL gets appmsgid)
        self.page.wait_for_timeout(1000)
        current_url = self.page.url
        if "appmsgid=" in current_url and "appmsgid=100000" in current_url:
            logger.info("Detected appmsgid in URL: draft likely saved")
            return {"success": True, "message": "保存成功", "draft_id": ""}

        logger.warning("Save may have failed - no appmsgid detected in URL: {}", current_url[:100])
        self._screenshot("save_uncertain")
        return {"success": False, "message": "无法确认保存成功"}

    # ===== Publish entry =====

    def publish_draft(self, article: WechatArticle) -> dict:
        logger.info("=" * 60)
        logger.info("Starting draft upload")
        logger.info("=" * 60)
        try:
            if not self.open_editor():
                return {
                    "success": False,
                    "message": "无法进入编辑器",
                    "screenshot": str(self._screenshot("fail_editor")),
                }
            if not self.fill_article(article):
                return {
                    "success": False,
                    "message": "填写文章失败",
                    "screenshot": str(self._screenshot("fail_fill")),
                }
            save_result = self.save_draft()
            if not save_result.get("success"):
                save_result["screenshot"] = str(self._screenshot("fail_save"))
            return save_result
        except Exception as e:
            logger.exception("Draft upload exception")
            return {
                "success": False,
                "message": str(e),
                "screenshot": str(self._screenshot("exception")),
            }

    def _safe_body_text(self) -> str:
        try:
            return self.page.locator("body").inner_text(timeout=2000) or ""
        except Exception:
            return ""

    def _screenshot(self, name: str) -> Path:
        path = self.SCREENSHOT_DIR / f"{name}_{int(time.time())}.png"
        try:
            self.page.screenshot(path=str(path))
        except Exception:
            pass
        return path


