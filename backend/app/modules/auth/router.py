"""账号接口。

调用时机：登录页二维码登录、顶部用户信息与账号管理页。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ok
from app.core.security import create_access_token, get_current_user, require_admin
from app.db.session import get_db
from app.modules.auth import service
from app.modules.auth.models import User
from app.modules.auth.schemas import DingTalkExchangeRequest, LoginResponse, UserOut, UserUpdateRequest

router = APIRouter(tags=["账号"])


@router.get("/api/auth/config")
def auth_config() -> dict:
    """返回扫码登录所需的公开参数。

    调用时机：登录页初始化二维码前；未配置凭据时 enabled=false，前端据此提示。
    """
    settings = get_settings()
    return ok(
        {
            "enabled": settings.dingtalk_enabled,
            "clientId": settings.dingtalk_client_id,
            "redirectUri": settings.dingtalk_redirect_uri,
        }
    )


@router.post("/api/auth/dingtalk/exchange")
def dingtalk_exchange(payload: DingTalkExchangeRequest, db: Session = Depends(get_db)) -> dict:
    """用扫码拿到的 authCode 换取登录令牌。"""
    user = service.login_with_dingtalk(db, payload.auth_code)
    token = create_access_token(str(user.id))
    db.commit()
    return ok(LoginResponse(access_token=token, user=UserOut.model_validate(user)).model_dump(mode="json"))


@router.get("/api/auth/me")
def me(user: User = Depends(get_current_user)) -> dict:
    """返回当前登录用户。"""
    return ok(UserOut.model_validate(user).model_dump(mode="json"))


@router.get("/api/users")
def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    """分页列出账号，仅管理员可用。"""
    users, total = service.list_users(db, page, size)
    return ok({"items": [UserOut.model_validate(u).model_dump(mode="json") for u in users], "total": total})


@router.patch("/api/users/{user_id}")
def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
) -> dict:
    """修改账号角色或启停，仅管理员可用。"""
    user = service.update_user(db, user_id, payload, actor)
    db.commit()
    return ok(UserOut.model_validate(user).model_dump(mode="json"))
