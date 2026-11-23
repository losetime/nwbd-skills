"""统一异常与响应结构。

调用时机：应用启动时注册异常处理器；业务代码通过抛出 AppError 表达可预期的失败。
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """可预期的业务错误，携带机器可读的 code 与可选明细。"""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []


def ok(data: Any = None, message: str = "ok") -> dict[str, Any]:
    """包装成功响应，前端据此统一解包 data。"""
    return {"code": 0, "message": message, "data": data}


def _error_body(code: str, message: str, details: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"code": code, "message": message, "details": details or []}


def register_exception_handlers(app: FastAPI) -> None:
    """调用时机：create_app 构建应用时注册，避免各路由重复处理异常。"""

    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"field": ".".join(str(p) for p in item.get("loc", [])), "message": item.get("msg", "")}
            for item in exc.errors()
        ]
        return JSONResponse(status_code=422, content=_error_body("VALIDATION_FAILED", "请求参数不合法", details))

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(code, str(exc.detail)),
        )
