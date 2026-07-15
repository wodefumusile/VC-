"""Playwright browser manager v3.1 - CDP mode with browser reference fix"""

import json, os, re, time
from pathlib import Path
from loguru import logger

from .config import USER_DATA_DIR, BROWSER_CONFIG, PAGE_TIMEOUT, set_token, get_token, BROWSER_CDP_URL

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
for c in [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]:
    if os.path.exists(c):
        CHROME_PATH = c
        break


class BrowserManager:
    """Manage Playwright browser lifecycle - v3.1 CDP with browser ref"""

    def __init__(self, user_data_dir: Path = USER_DATA_DIR, cdp_url: str = None):
        self.user_data_dir = Path(user_data_dir)
        self.cdp_url = cdp_url or BROWSER_CDP_URL
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self._storage_file = self.user_data_dir.parent / "auth_state.json"
        self._full_session_file = self.user_data_dir.parent / "full_session.json"
        self._playwright = None
        self._browser = None  # CRITICAL: keep browser reference for CDP mode
        self._context = None
        self._page = None
        self._started = False
        self._chrome_path = CHROME_PATH
        self._use_cdp = bool(self.cdp_url)

    def _get_sync_playwright(self):
        from playwright.sync_api import sync_playwright
        if not self._playwright:
            self._playwright = sync_playwright().start()
        return self._playwright

    def start(self):
        if self._use_cdp:
            return self._start_cdp()
        return self._start_local()

    def _start_cdp(self):
        """Connect to existing Chrome via CDP (in-app browser mode)."""
        logger.info("=" * 50)
        logger.info("Connecting to EXISTING Chrome via CDP")
        logger.info("  CDP URL: {}", self.cdp_url)
        logger.info("=" * 50)

        if self._started and self._context:
            # Verify context is still alive
            try:
                _ = len(self._context.pages)  # Quick health check
                logger.info("CDP context still alive, reusing")
                return self._context
            except Exception:
                logger.warning("CDP context dead, reconnecting...")
                self._started = False

        pw = self._get_sync_playwright()
        try:
            logger.info("Connecting over CDP...")
            self._browser = pw.chromium.connect_over_cdp(self.cdp_url)  # KEEP REFERENCE!
            logger.success("Connected to existing Chrome | contexts={}", len(self._browser.contexts))

            # Use the first existing context (has WeChat session)
            if self._browser.contexts:
                self._context = self._browser.contexts[0]
                logger.info("Using existing context | pages={}", len(self._context.pages))
            else:
                self._context = self._browser.new_context()
                logger.info("Created new context")

            self._context.set_default_timeout(PAGE_TIMEOUT)
            self._started = True

            # Extract token from existing WeChat pages
            for page in self._context.pages:
                url = page.url
                if "mp.weixin.qq.com" in url and "token=" in url:
                    m = re.search(r'token=(\d+)', url)
                    if m:
                        set_token(m.group(1))
                        logger.info("Extracted WeChat token: {}...", m.group(1)[:20])
                        break

            logger.success("CDP browser ready | token={}", (get_token() or "")[:20])
            return self._context
        except Exception as e:
            logger.exception("CDP connection failed: {}", e)
            logger.warning("Falling back to local Chrome launch...")
            self._use_cdp = False
            return self._start_local()

    def _start_local(self):
        """Original: launch new Chrome instance."""
        logger.info("=" * 50)
        logger.info("Starting Chrome (local mode)")
        logger.info("  exe: {}", self._chrome_path)
        logger.info("  profile: {}", self.user_data_dir)
        logger.info("=" * 50)

        if self._started and self._context:
            return self._context

        if not self._chrome_path or not os.path.exists(self._chrome_path):
            raise RuntimeError(f"Chrome not found at {self._chrome_path}")

        pw = self._get_sync_playwright()
        launch_kwargs = {
            "user_data_dir": str(self.user_data_dir),
            "headless": BROWSER_CONFIG["headless"],
            "viewport": BROWSER_CONFIG["viewport"],
            "locale": BROWSER_CONFIG["locale"],
            "executable_path": self._chrome_path,
            "ignore_default_args": ["--enable-automation"],
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--disable-component-extensions-with-background-pages",
                "--disable-background-networking",
                "--disable-sync",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-features=ChromeWhatsNewUI",
            ],
        }
        try:
            self._context = pw.chromium.launch_persistent_context(**launch_kwargs)
            self._context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """)
            logger.info("  stealth: webdriver=undefined")
            self._context.set_default_timeout(PAGE_TIMEOUT)
            self._started = True

            if self._storage_file.exists():
                try:
                    state = json.loads(self._storage_file.read_text(encoding="utf-8"))
                    cookies = state.get("cookies", [])
                    if cookies:
                        self._context.add_cookies(cookies)
                        logger.info("  cookies restored: {}", len(cookies))
                        saved_token = state.get("_token")
                        if saved_token:
                            set_token(saved_token)
                            logger.info("  token restored: {}...", saved_token[:20])
                except Exception as e:
                    logger.warning("Cookie restore failed: {}", e)

            logger.success("Chrome started (local)")
            return self._context
        except Exception as e:
            logger.exception("Start failed")
            raise RuntimeError(str(e)) from e

    def new_page(self):
        if not self._context:
            self.start()
        # For CDP mode: check if context is still alive, reconnect if needed
        if self._use_cdp:
            try:
                _ = len(self._context.pages)
            except Exception:
                logger.warning("CDP context dead in new_page, reconnecting...")
                self._started = False
                self._context = None
                self.start()
        page = self._context.new_page()
        self._page = page
        return page

    def save_auth(self, page=None):
        if not self._context:
            return False
        if self._use_cdp:
            logger.info("CDP mode: session already in shared browser context")
            return True
        try:
            state = self._context.storage_state()
            state["_token"] = get_token()
            state["_saved_at"] = time.time()
            p = page or self._page
            if p:
                try:
                    state["localStorage"] = p.evaluate("() => { return JSON.stringify(localStorage); }")
                except Exception:
                    pass
                try:
                    state["sessionStorage"] = p.evaluate("() => { return JSON.stringify(sessionStorage); }")
                except Exception:
                    pass
            self._storage_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info("Auth saved: {} cookies", cookie_count := len(state.get("cookies", [])))
            return True
        except Exception as e:
            logger.warning("Auth save failed: {}", e)
            return False

    def close(self, page=None):
        if not self._use_cdp:
            self.save_auth(page)
        try:
            if self._page:
                self._page.close()
            if self._context and not self._use_cdp:
                self._context.close()
            if self._browser and not self._use_cdp:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None
            self._started = False
        except Exception as e:
            logger.warning("Close error: {}", e)

    @property
    def context(self):
        return self._context

    @property
    def page(self):
        return self._page

    @property
    def is_running(self):
        return self._started and self._context is not None


browser_manager = BrowserManager()
