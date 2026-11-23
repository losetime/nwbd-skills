"""账号业务规则。

调用时机：钉钉扫码登录、首次启动初始化管理员、用户管理接口。
"""

from __future__ import annotations

import secrets

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import hash_password
from app.modules.audit.service import record
from app.modules.auth import repository
from app.modules.auth.models import User
from app.modules.auth.schemas import UserUpdateRequest
from app.modules.dingtalk import client as dingtalk


def sync_dingtalk_roles(db: Session, actor: User | None = None) -> None:
    """按钉钉管理员列表刷新本地角色。

    调用时机：每次扫码登录后；拉取失败时保持原角色，不影响登录。
    只有绑定过钉钉的账号参与同步，历史密码账号不受影响。
    额外管理员按 dingtalk_user_id / dingtalk_union_id 精确匹配，不按显示名。
    """
    settings = get_settings()
    try:
        admin_ids = dingtalk.list_admin_ids()
    except AppError:
        return

    extras = {item.strip() for item in settings.dingtalk_extra_admins.split(",") if item.strip()}
    for row in repository.list_all(db):
        if not row.dingtalk_user_id:
            continue
        matched = row.dingtalk_user_id in admin_ids
        if not matched and extras:
            matched = bool(row.dingtalk_user_id in extras or row.dingtalk_union_id in extras)
        role = "admin" if matched else "member"
        if row.role == role:
            continue
        row.role = role
        if actor is not None:
            record(
                db,
                actor,
                "user_update",
                detail={"username": row.username, "changes": {"role": role, "via": "dingtalk"}},
            )


def login_with_dingtalk(db: Session, auth_code: str) -> User:
    """扫码登录：换取钉钉身份，必要时自动建号，并同步角色。

    调用时机：前端拿到 authCode 后调用；首次登录默认成员，管理员以钉钉管理员列表为准。
    """
    settings = get_settings()
    if not settings.dingtalk_enabled:
        raise AppError("DINGTALK_DISABLED", "未配置钉钉登录", 503)

    profile = dingtalk.exchange_code(auth_code)
    if not profile.active:
        raise AppError("DINGTALK_USER_DISABLED", "该钉钉账号已停用", 403)

    user = repository.get_by_dingtalk_union_id(db, profile.union_id)
    if user is None:
        # 兼容预建账号：只有 userId、还没绑 unionId
        user = repository.get_by_dingtalk_user_id(db, profile.user_id)
    if user is None:
        username = profile.user_id
        if repository.get_by_username(db, username) is not None:
            username = f"dt_{profile.union_id[:16]}"
        user = User(
            username=username,
            password_hash=hash_password(secrets.token_urlsafe(24)),
            display_name=profile.name,
            role="member",
            dingtalk_union_id=profile.union_id,
            dingtalk_user_id=profile.user_id,
        )
        repository.create_user(db, user)
        record(db, user, "register", detail={"username": user.username, "via": "dingtalk"})
    else:
        user.display_name = profile.name or user.display_name
        user.dingtalk_user_id = profile.user_id
        user.dingtalk_union_id = profile.union_id
        if not user.enabled:
            raise AppError("USER_DISABLED", "该账号已被停用", 403)

    sync_dingtalk_roles(db, actor=user)
    return user


def bootstrap_admin(db: Session) -> None:
    """首次启动时创建初始管理员。

    调用时机：应用启动阶段，表为空时才创建，已存在则跳过。
    该账号仅用于承接历史技能归属，不再支持密码登录。
    """
    settings = get_settings()
    if repository.get_by_username(db, settings.bootstrap_admin_username) is not None:
        return
    user = User(
        username=settings.bootstrap_admin_username,
        password_hash=hash_password(settings.bootstrap_admin_password),
        display_name="管理员",
        role="admin",
    )
    repository.create_user(db, user)
    record(db, None, "user_create", detail={"username": user.username, "bootstrap": True})
    db.commit()


def update_user(db: Session, user_id: str, payload: UserUpdateRequest, actor: User) -> User:
    """修改角色或启停状态，任一变化都记录审计。

    调用时机：账号页切换角色或启停；角色会在下次钉钉登录时按钉钉管理员列表覆盖。
    """
    user = repository.get_user(db, user_id)
    if user is None:
        raise AppError("USER_NOT_FOUND", "账号不存在", 404)
    changes: dict[str, object] = {}
    if payload.role is not None and payload.role != user.role:
        user.role = payload.role
        changes["role"] = payload.role
    if payload.enabled is not None and payload.enabled != user.enabled:
        user.enabled = payload.enabled
        changes["enabled"] = payload.enabled
    if changes:
        record(db, actor, "user_update", detail={"username": user.username, "changes": changes})
    return user


def list_users(db: Session, page: int, size: int) -> tuple[list[User], int]:
    """分页查询账号列表。"""
    return repository.list_users(db, (page - 1) * size, size)
