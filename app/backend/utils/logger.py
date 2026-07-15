"""
统一日志系统 — 基于 Loguru

支持：
- 控制台彩色输出
- 按模块分文件保存
- 错误日志单独记录
"""

import sys
from pathlib import Path
from loguru import logger

from backend.config import settings


def setup_logger():
    """配置日志系统"""
    # 移除默认 handler
    logger.remove()

    # 日志目录
    log_dir = settings.LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    # 控制台输出（彩色）
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True,
    )

    # 全量日志文件
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
    )

    # 文章生成日志
    logger.add(
        log_dir / "article_generate_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
    )

    # 微信发布日志
    logger.add(
        log_dir / "wechat_publish_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
    )

    # 工作流日志
    logger.add(
        log_dir / "workflow_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
    )

    # 错误日志（ERROR 及以上）
    logger.add(
        log_dir / "error_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{line} | {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
    )

    logger.info("日志系统初始化完成 | log_dir={}", log_dir)