import sys
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from loguru import logger

from backend.config import settings
from backend.utils.logger import setup_logger
from backend.utils.exceptions import (
    success_response, AppError,
    app_error_handler, validation_error_handler, general_error_handler,
)
from backend.api.article import router as article_router
from backend.api.publish import router as publish_router
from backend.api.tasks import router as tasks_router
from backend.api.v2 import router as v2_router
from backend.web_ui import WEB_PAGE_HTML


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    _startup_check()
    _start_backup_scheduler()
    logger.info("{} v{} starting", settings.APP_NAME, settings.APP_VERSION)
    from publish_engine.core.playwright_service import playwright_service
    await playwright_service.start()
    from backend.services.task_queue import publish_queue
    await publish_queue.start()
    yield
    await publish_queue.stop()
    await playwright_service.stop()
    logger.info("{} shutdown", settings.APP_NAME)


app = FastAPI(
    title="WeChat AI Publisher",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if not settings.CLIENT_MODE else None,
    redoc_url=None,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, general_error_handler)

# v1 routes (unchanged)
app.include_router(article_router)
app.include_router(publish_router)
app.include_router(tasks_router)

# v2 routes
app.include_router(v2_router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve web UI with admin token injected."""
    html = WEB_PAGE_HTML.replace("__ADMIN_TOKEN_PLACEHOLDER__", settings.ADMIN_TOKEN)
    return HTMLResponse(html)


@app.get("/health")
async def health():
    from publish_engine.core.playwright_service import playwright_service
    from backend.services.task_queue import publish_queue
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "browser": playwright_service.health_report(),
        "queue": {
            "worker_running": publish_queue._worker_task is not None
            and not publish_queue._worker_task.done()
        },
        "v2": {
            "image_provider": settings.IMAGE_PROVIDER,
            "formatter_templates": ["technology", "business", "knowledge", "personal"],
        },
    }


@app.get("/show-drafts")
async def show_drafts():
    """Open drafts page in the Chrome window — KEEPS IT VISIBLE"""
    from publish_engine.core.playwright_service import playwright_service
    from publish_engine.browser.config import get_token
    token = get_token() or "563830899"
    url = (f"https://mp.weixin.qq.com/cgi-bin/appmsg?"
           f"begin=0&count=10&type=77&action=list_card&token={token}&lang=zh_CN")
    result = await playwright_service.show_page(url)
    return {"success": True, "url": result["url"], "title": result["title"],
            "message": "CHECK THE CHROME WINDOW!"}


def _startup_check():
    """Validate critical config on startup."""
    from backend.config import settings
    issues = []
    if not settings.AI_API_KEY or settings.AI_API_KEY.startswith('your-'):
        issues.append("AI_API_KEY not configured - AI features will fail — configure in .env or Web UI)")
    if not settings.ADMIN_TOKEN or settings.ADMIN_TOKEN == "admin-token-change-me":
        issues.append("ADMIN_TOKEN is default value (change it!)")
    if issues:
        logger.warning("=" * 50)
        logger.warning("STARTUP CHECK FAILED:")
        for i in issues:
            logger.warning(f"  - {i}")
        logger.warning("Configure .env and restart.")
        logger.warning("=" * 50)
    else:
        logger.info("Startup check passed: AI_API_KEY + ADMIN_TOKEN configured")
    logger.info("Mode: {} | Image: {} | Knowledge: {}",
                 "AI Full" if settings.image_enabled else "Text Only",
                 "enabled" if settings.image_enabled else "disabled",
                 "enabled" if settings.obsidian_enabled else "disabled")


def _start_backup_scheduler():
    """Schedule daily database backup."""
    import asyncio
    from pathlib import Path
    from datetime import datetime

    async def daily_backup():
        while True:
            await asyncio.sleep(86400)  # 24 hours
            try:
                db_path = Path(__file__).parent.parent / "storage" / "articles.db"
                backup_dir = Path(__file__).parent.parent / "backup"
                backup_dir.mkdir(exist_ok=True)
                if db_path.exists():
                    date_str = datetime.now().strftime("%Y%m%d")
                    backup_path = backup_dir / f"articles_{date_str}.db"
                    import shutil
                    shutil.copy2(db_path, backup_path)
                    logger.info("Database backup saved: {}", backup_path.name)
            except Exception as e:
                logger.warning("Backup failed: {}", e)

    asyncio.create_task(daily_backup())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.SERVER_HOST,
                port=settings.SERVER_PORT, reload=settings.is_dev,
                log_level=settings.LOG_LEVEL.lower())
