"""账号数据访问。

调用时机：登录校验、令牌解析、用户管理接口中读写 app_user 表。
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.auth.models import User


def get_user(db: Session, user_id: str) -> User | None:
    """按主键取用户，令牌解析后调用。"""
    return db.get(User, user_id)


def get_by_username(db: Session, username: str) -> User | None:
    """按用户名取用户，登录时调用。"""
    return db.scalar(select(User).where(User.username == username))


def get_by_dingtalk_union_id(db: Session, union_id: str) -> User | None:
    """按钉钉 unionId 取用户，扫码登录时调用。"""
    return db.scalar(select(User).where(User.dingtalk_union_id == union_id))


def get_by_dingtalk_user_id(db: Session, user_id: str) -> User | None:
    """按钉钉 userId 取用户，用于预建账号或 unionId 补齐。"""
    return db.scalar(select(User).where(User.dingtalk_user_id == user_id))


def get_users_by_ids(db: Session, user_ids: list[uuid.UUID]) -> dict[str, User]:
    """按主键批量取用户，列表页解析所属人时调用，避免逐条查询。"""
    if not user_ids:
        return {}
    rows = db.scalars(select(User).where(User.id.in_(user_ids))).all()
    return {str(row.id): row for row in rows}


def list_all(db: Session) -> list[User]:
    """取全部用户，同步钉钉角色时调用。"""
    return list(db.scalars(select(User)).all())


def create_user(db: Session, user: User) -> User:
    """写入新用户并返回带主键的实例。"""
    db.add(user)
    db.flush()
    return user


def list_users(db: Session, offset: int, limit: int) -> tuple[list[User], int]:
    """分页列出用户，用户管理页调用。"""
    total = db.scalar(select(func.count()).select_from(User)) or 0
    rows = db.scalars(select(User).order_by(User.created_at).offset(offset).limit(limit)).all()
    return list(rows), total
