"""应用入口。

调用时机：uvicorn 启动时构建 FastAPI 实例，注册路由、异常处理与启动初始化。
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.core.errors import ok, register_exception_handlers
from app.db.session import SessionLocal, engine
from app.modules.audit.router import router as audit_router
from app.modules.auth import service as auth_service
from app.modules.auth.router import router as auth_router
from app.modules.skill.router import router as skill_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """启动时确认数据库可达、创建数据目录并初始化管理员。"""
    settings = get_settings()
    settings.ensure_dirs()
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    with SessionLocal() as db:
        auth_service.bootstrap_admin(db)
    yield


def create_app() -> FastAPI:
    """构建应用实例。

    调用时机：模块导入时执行一次，uvicorn 以此作为 ASGI 入口。
    """
    settings = get_settings()
    app = FastAPI(
        title="nwbd-skills",
        description="技能包注册、校验、版本与发布服务",
        version="0.1.0",
        lifespan=lifespan,
    )

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    register_exception_handlers(app)
    app.include_router(auth_router)
    app.include_router(skill_router)
    app.include_router(audit_router)

    @app.get("/api/health")
    def health() -> dict:
        """健康检查，供容器探针与 Nginx 使用。"""
        return ok({"status": "up"})

    return app


app = create_app()
