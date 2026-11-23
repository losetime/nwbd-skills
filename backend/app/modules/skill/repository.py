"""技能数据访问。

调用时机：技能模块的列表、详情、版本读写与统计。
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.skill.models import Skill, SkillComment, SkillVersion


def get_by_name(db: Session, name: str) -> Skill | None:
    """按技能名取技能，上传新版本与详情接口调用。"""
    return db.scalar(select(Skill).where(Skill.name == name))


def create_skill(db: Session, skill: Skill) -> Skill:
    """写入新技能。"""
    db.add(skill)
    db.flush()
    return skill


def create_version(db: Session, version: SkillVersion) -> SkillVersion:
    """写入新版本。"""
    db.add(version)
    db.flush()
    return version


def get_version(db: Session, skill_id: uuid.UUID, version: int) -> SkillVersion | None:
    """按技能与版本号取版本。"""
    return db.scalar(select(SkillVersion).where(SkillVersion.skill_id == skill_id, SkillVersion.version == version))


def get_version_by_id(db: Session, version_id: uuid.UUID | None) -> SkillVersion | None:
    """按主键取版本，解析 current_version 时调用。"""
    if version_id is None:
        return None
    return db.get(SkillVersion, version_id)


def list_versions(db: Session, skill_id: uuid.UUID) -> list[SkillVersion]:
    """取技能全部版本，按版本号倒序。"""
    return list(db.scalars(select(SkillVersion).where(SkillVersion.skill_id == skill_id).order_by(SkillVersion.version.desc())).all())


def next_version_number(db: Session, skill_id: uuid.UUID) -> int:
    """计算下一个版本号，取当前最大值加一。"""
    current = db.scalar(select(func.max(SkillVersion.version)).where(SkillVersion.skill_id == skill_id))
    return int(current or 0) + 1


def find_same_digest(db: Session, skill_id: uuid.UUID, digest: str) -> SkillVersion | None:
    """查找内容相同的既有版本，用于提示重复上传。"""
    return db.scalar(
        select(SkillVersion).where(SkillVersion.skill_id == skill_id, SkillVersion.package_sha256 == digest).limit(1)
    )


def list_skills(db: Session, *, q: str | None, status: str | None, offset: int, limit: int) -> tuple[list[Skill], int]:
    """按关键词与状态过滤，按更新时间倒序分页。"""
    stmt = select(Skill)
    count_stmt = select(func.count()).select_from(Skill)
    if q:
        pattern = f"%{q}%"
        condition = or_(Skill.name.ilike(pattern), Skill.summary.ilike(pattern), Skill.display_name.ilike(pattern))
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)
    if status:
        stmt = stmt.where(Skill.status == status)
        count_stmt = count_stmt.where(Skill.status == status)
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(stmt.order_by(Skill.updated_at.desc()).offset(offset).limit(limit)).all()
    return list(rows), total


def current_versions(db: Session, skills: Sequence[Skill]) -> dict[uuid.UUID, SkillVersion]:
    """批量取当前发布版本，避免列表页逐条查询。"""
    ids = [s.current_version_id for s in skills if s.current_version_id]
    if not ids:
        return {}
    rows = db.scalars(select(SkillVersion).where(SkillVersion.id.in_(ids))).all()
    return {row.id: row for row in rows}


def version_counts(db: Session, skills: Sequence[Skill]) -> dict[uuid.UUID, int]:
    """批量统计版本数量。"""
    ids = [s.id for s in skills]
    if not ids:
        return {}
    rows = db.execute(
        select(SkillVersion.skill_id, func.count()).where(SkillVersion.skill_id.in_(ids)).group_by(SkillVersion.skill_id)
    ).all()
    return {row[0]: int(row[1]) for row in rows}


def latest_versions(db: Session, skills: Sequence[Skill]) -> dict[uuid.UUID, SkillVersion]:
    """批量取最新版本，用于尚未发布时展示体积与文件数。"""
    ids = [s.id for s in skills]
    if not ids:
        return {}
    rows = db.scalars(
        select(SkillVersion)
        .where(SkillVersion.skill_id.in_(ids))
        .order_by(SkillVersion.skill_id, SkillVersion.version.desc())
    ).all()
    result: dict[uuid.UUID, SkillVersion] = {}
    for row in rows:
        result.setdefault(row.skill_id, row)
    return result


def list_comments(db: Session, skill_id: uuid.UUID, offset: int, limit: int) -> tuple[list[SkillComment], int]:
    """按技能分页取评论，时间倒序。"""
    total = db.scalar(select(func.count()).select_from(SkillComment).where(SkillComment.skill_id == skill_id)) or 0
    rows = db.scalars(
        select(SkillComment)
        .where(SkillComment.skill_id == skill_id)
        .order_by(SkillComment.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return list(rows), int(total)


def create_comment(db: Session, comment: SkillComment) -> SkillComment:
    """写入一条评论。"""
    db.add(comment)
    db.flush()
    return comment


def get_comment(db: Session, comment_id: uuid.UUID) -> SkillComment | None:
    """按主键取评论，删除权限校验用。"""
    return db.get(SkillComment, comment_id)


def delete_comment(db: Session, comment: SkillComment) -> None:
    """删除评论。"""
    db.delete(comment)


def count_skills(db: Session) -> int:
    """统计技能总数，概览页调用。"""
    return int(db.scalar(select(func.count()).select_from(Skill)) or 0)


def count_versions(db: Session) -> int:
    """统计版本总数，概览页调用。"""
    return int(db.scalar(select(func.count()).select_from(SkillVersion)) or 0)


def published_skills(db: Session) -> list[Skill]:
    """取全部已发布技能，生成机器可读索引时调用。"""
    return list(db.scalars(select(Skill).where(Skill.current_version_id.is_not(None)).order_by(Skill.name)).all())
