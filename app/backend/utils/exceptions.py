"""
统一响应格式 & 异常处理

所有 API 返回统一结构：
- 成功: {"success": true, "data": {...}}
- 失败: {"success": false, "error": {"code": "...", "message": "..."}}

v2.1.1: 生产环境不泄露 traceback
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger

from backend.config import settings


class AppError(Exception):
    """业务异常基类"""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code


# --- 统一错误码 ---
class ErrorCode:
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    UNAUTHORIZED = "UNAUTHORIZED"
    LOGIN_EXPIRED = "LOGIN_EXPIRED"
    BROWSER_ERROR = "BROWSER_ERROR"
    AI_API_ERROR = "AI_API_ERROR"
    CONFIG_ERROR = "CONFIG_ERROR"


def success_response(data=None, message: str = "ok"):
    """成功响应"""
    return JSONResponse(
        status_code=200,
        content={"success": True, "data": data, "message": message},
    )


def error_response(code: str, message: str, status_code: int = 400):
    """失败响应"""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {"code": code, "message": message},
        },
    )


async def app_error_handler(request: Request, exc: AppError):
    """捕获自定义业务异常"""
    logger.warning("业务异常 | path={} code={} | {}", request.url.path, exc.code, exc.message)
    return error_response(exc.code, exc.message, exc.status_code)


async def validation_error_handler(request: Request, exc: RequestValidationError):
    """捕获请求校验异常"""
    msg = str(exc.errors()[0]["msg"]) if exc.errors() else "请求参数错误"
    logger.warning("参数校验失败 | path={} | {}", request.url.path, msg)
    return error_response(ErrorCode.VALIDATION_ERROR, msg, 422)


async def general_error_handler(request: Request, exc: Exception):
    """捕获未预期的异常 — 生产环境不泄露堆栈"""
    logger.exception("未处理异常 | path={} | error={}", request.url.path, str(exc))

    if settings.is_prod:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            "服务器内部错误，请联系管理员",
            500,
        )
    else:
        # 开发环境返回详细信息
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"内部错误: {type(exc).__name__}: {str(exc)}",
            500,
        )
