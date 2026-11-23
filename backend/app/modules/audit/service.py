"""审计写入与查询。

调用时机：所有写操作成功后与登录成功/失败时调用；管理员在审计页按条件查询。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog


def record(
    db: Session,
    actor: Any,
    action: str,
    *,
    skill: Any = None,
    version: int | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    """写入一条审计记录。

    调用时机：业务写操作内、提交事务之前调用，保证与业务变更同生共死。
    """
    entry = AuditLog(
        actor_id=getattr(actor, "id", None),
        actor_name=getattr(actor, "username", None) or (detail or {}).get("username", ""),
        action=action,
        skill_id=getattr(skill, "id", None),
        skill_name=getattr(skill, "name", ""),
        version=version,
        detail=detail or {},
    )
    db.add(entry)


def query(
    db: Session,
    *,
    action: str | None,
    skill_name: str | None,
    page: int,
    size: int,
) -> tuple[list[AuditLog], int]:
    """按动作与技能名过滤审计记录，按时间倒序分页。"""
    stmt = select(AuditLog)
    count_stmt = select(func.count()).select_from(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action)
        count_stmt = count_stmt.where(AuditLog.action == action)
    if skill_name:
        stmt = stmt.where(AuditLog.skill_name == skill_name)
        count_stmt = count_stmt.where(AuditLog.skill_name == skill_name)
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(
        stmt.order_by(AuditLog.created_at.desc()).offset((page - 1) * size).limit(size)
    ).all()
    return list(rows), total


def recent(db: Session, limit: int = 8) -> list[AuditLog]:
    """取最近若干条记录，概览页调用。"""
    return list(db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).all())
