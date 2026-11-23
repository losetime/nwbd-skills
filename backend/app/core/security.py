"""密码哈希与访问令牌。

调用时机：登录时校验口令并签发令牌；受保护接口通过 get_current_user 解析令牌。
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.session import get_db

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.modules.auth.models import User

_hasher = PasswordHasher()
_bearer = HTTPBearer(auto_error=False)


def hash_password(raw: str) -> str:
    """生成 argon2 口令哈希，注册与改密时调用。"""
    return _hasher.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    """校验明文口令，任何解析异常都视为不匹配。"""
    try:
        return _hasher.verify(hashed, raw)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_access_token(user_id: str) -> str:
    """签发访问令牌，登录成功后返回给客户端。"""
    settings = get_settings()
    now = dt.datetime.now(dt.UTC)
    payload: dict[str, Any] = {
        "sub": user_id,
        "iat": now,
        "exp": now + dt.timedelta(minutes=settings.token_ttl_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> str:
    """解析令牌并返回用户 ID，失败统一抛 401。"""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise AppError("TOKEN_EXPIRED", "登录已过期，请重新登录", 401) from exc
    except jwt.PyJWTError as exc:
        raise AppError("TOKEN_INVALID", "登录状态无效", 401) from exc
    subject = payload.get("sub")
    if not subject:
        raise AppError("TOKEN_INVALID", "登录状态无效", 401)
    return str(subject)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """解析当前登录用户。

    调用时机：所有需要身份的路由作为依赖注入，未登录直接抛 401。
    """
    from app.modules.auth.repository import get_user

    if credentials is None or not credentials.credentials:
        raise AppError("UNAUTHORIZED", "请先登录", 401)
    user_id = decode_token(credentials.credentials)
    user = get_user(db, user_id)
    if user is None or not user.enabled:
        raise AppError("UNAUTHORIZED", "账号不存在或已停用", 401)
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """仅允许管理员调用。

    调用时机：用户管理、归档等高权限路由作为依赖注入。
    """
    if user.role != "admin":
        raise AppError("FORBIDDEN", "需要管理员权限", 403)
    return user
