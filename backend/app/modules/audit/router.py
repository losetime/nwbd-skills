"""审计接口。

调用时机：管理员在审计页按动作、技能与分页条件查询历史操作。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.errors import ok
from app.core.security import require_admin
from app.db.session import get_db
from app.modules.audit import service
from app.modules.auth.models import User

router = APIRouter(tags=["审计"])


@router.get("/api/audit")
def list_audit(
    action: str | None = Query(None, max_length=32),
    skill_name: str | None = Query(None, max_length=64),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    """分页查询审计记录，仅管理员可用。"""
    rows, total = service.query(db, action=action, skill_name=skill_name, page=page, size=size)
    return ok(
        {
            "items": [
                {
                    "id": str(row.id),
                    "action": row.action,
                    "actor": row.actor_name,
                    "skill": row.skill_name,
                    "version": row.version,
                    "detail": row.detail,
                    "at": row.created_at.isoformat(),
                }
                for row in rows
            ],
            "total": total,
        }
    )
