"""Playwright Service -- singleton with DEDICATED thread."""

import asyncio
import queue
import threading
import time
from pathlib import Path
from typing import Callable, Any
from loguru import logger

from publish_engine.browser.browser_manager import BrowserManager
from publish_engine.browser.config import USER_DATA_DIR


class PlaywrightService:

    def __init__(self):
        self._thread: threading.Thread | None = None
        self._queue: queue.Queue = queue.Queue()
        self._lock = asyncio.Lock()
        self._started = False
        self._start_time: float = 0
        self._manager: BrowserManager | None = None
        self._last_page = None  # Keep reference to visible page

    async def start(self) -> None:
        async with self._lock:
            if self._started:
                return
            logger.info("PlaywrightService starting dedicated thread...")
            self._thread = threading.Thread(target=self._run_loop, name="playwright-dedicated", daemon=False)
            self._thread.start()
            self._started = True
            self._start_time = time.time()

    def _run_loop(self):
        logger.info("Playwright dedicated thread started")
        self._manager = BrowserManager()
        self._manager.start()

        # Navigate Chrome to the Web UI dashboard — single window for everything
        try:
            page = self._manager.new_page()
            page.goto("http://127.0.0.1:8000", wait_until="domcontentloaded", timeout=10000)
            self._last_page = page
            # Close initial about:blank page so only dashboard remains
            for p in self._manager.context.pages:
                if p != page and (p.url == "about:blank" or p.url == ""):
                    p.close()
            logger.info("Dashboard opened in Chrome")
        except Exception as e:
            logger.warning("Failed to open dashboard in Chrome: {}", e)

        logger.success("PlaywrightService ready | profile={}", USER_DATA_DIR)
        while True:
            item = self._queue.get()
            if item is None:
                break
            loop, future, fn, keep_open = item
            try:
                page = self._manager.new_page()
                if keep_open:
                    self._last_page = page
                try:
                    result = fn(page)
                    loop.call_soon_threadsafe(future.set_result, result)
                finally:
                    if not keep_open:
                        try:
                            page.close()
                        except Exception:
                            pass
            except Exception as e:
                loop.call_soon_threadsafe(future.set_exception, e)
        logger.info("Playwright dedicated thread stopping...")
        try:
            self._manager.close()
        except Exception:
            pass
        logger.info("Playwright dedicated thread stopped")

    async def stop(self) -> None:
        async with self._lock:
            if not self._started:
                return
            logger.info("PlaywrightService stopping...")
            self._queue.put(None)
            if self._thread:
                self._thread.join(timeout=10)
            self._started = False

    async def run_with_page(self, fn: Callable[..., Any], keep_open: bool = False) -> Any:
        if not self._started:
            await self.start()
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._queue.put((loop, future, fn, keep_open))
        return await future

    async def show_page(self, url: str) -> dict:
        """Navigate and KEEP the page open for the user to see."""
        def nav(page):
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(3000)
            return {"url": page.url, "title": page.title()}
        return await self.run_with_page(nav, keep_open=True)

    async def save_auth(self) -> bool:
        if not self._started:
            return False
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        def _save(page):
            return self._manager.save_auth() if self._manager else False
        self._queue.put((loop, future, _save, False))
        return await future

    @property
    def is_running(self) -> bool:
        return self._started

    @property
    def uptime(self) -> float:
        return time.time() - self._start_time if self._started else 0

    def health_report(self) -> dict:
        return {
            "started": self._started,
            "running": self._started and self._thread is not None and self._thread.is_alive(),
            "uptime_seconds": round(self.uptime, 1),
            "profile": str(USER_DATA_DIR),
        }


playwright_service = PlaywrightService()