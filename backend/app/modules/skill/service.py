"""技能业务规则。

调用时机：上传、发布、废弃、回滚、归档，以及列表、详情、文件与下载读取。
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.audit.service import record
from app.modules.auth.models import User
from app.modules.package import storage
from app.modules.package.validator import ensure_valid, validate_package
from app.modules.skill import repository
from app.modules.skill.models import Skill, SkillComment, SkillVersion
from app.modules.skill.schemas import (
    CommentCreate,
    CommentOut,
    FileEntry,
    SkillDetail,
    SkillListItem,
    UploadResult,
    VersionOut,
)


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def _current_version(db: Session, skill: Skill) -> SkillVersion | None:
    """取技能当前发布版本。"""
    return repository.get_version_by_id(db, skill.current_version_id)


def _require_skill(db: Session, name: str) -> Skill:
    """取技能，不存在时抛 404。"""
    skill = repository.get_by_name(db, name)
    if skill is None:
        raise AppError("SKILL_NOT_FOUND", "技能不存在", 404)
    return skill


def _require_manager(skill: Skill, actor: User) -> None:
    """校验当前用户能否管理该技能。

    调用时机：上传版本、发布、废弃、恢复、删除等写操作前；管理员与创建者放行。
    """
    if actor.role == "admin":
        return
    if skill.created_by is None or str(skill.created_by) != str(actor.id):
        raise AppError("FORBIDDEN", "只有创建者可以管理该技能", 403)


def _require_version(db: Session, skill: Skill, version: int | None) -> SkillVersion:
    """按版本号取版本，未指定时取当前发布版本。"""
    if version is None:
        current = _current_version(db, skill)
        if current is None:
            raise AppError("VERSION_NOT_FOUND", "该技能还没有已发布版本", 404)
        return current
    row = repository.get_version(db, skill.id, version)
    if row is None:
        raise AppError("VERSION_NOT_FOUND", f"版本 v{version} 不存在", 404)
    return row


def _to_item(
    skill: Skill, version: SkillVersion | None, version_count: int, current: SkillVersion | None = None
) -> SkillListItem:
    return SkillListItem(
        name=skill.name,
        display_name=skill.display_name or skill.name,
        summary=skill.summary,
        status=skill.status,
        version_count=version_count,
        current_version=current.version if current else None,
        file_count=version.file_count if version else 0,
        size_bytes=version.size_bytes if version else 0,
        updated_at=skill.updated_at,
    )


def list_skills(db: Session, *, q: str | None, status: str | None, page: int, size: int) -> tuple[list[SkillListItem], int]:
    """分页查询技能列表。"""
    skills, total = repository.list_skills(db, q=q, status=status, offset=(page - 1) * size, limit=size)
    currents = repository.current_versions(db, skills)
    latest = repository.latest_versions(db, skills)
    counts = repository.version_counts(db, skills)
    items = []
    for skill in skills:
        current = currents.get(skill.current_version_id) if skill.current_version_id else None
        items.append(_to_item(skill, current or latest.get(skill.id), counts.get(skill.id, 0), current))
    return items, total


def get_detail(db: Session, name: str) -> SkillDetail:
    """取技能详情与全部版本。"""
    skill = _require_skill(db, name)
    versions = repository.list_versions(db, skill.id)
    current = _current_version(db, skill)
    return SkillDetail(
        name=skill.name,
        display_name=skill.display_name or skill.name,
        summary=skill.summary,
        status=skill.status,
        current_version=current.version if current else None,
        created_by=skill.created_by,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
        versions=[
            VersionOut(
                version=v.version,
                status=v.status,
                changelog=v.changelog,
                size_bytes=v.size_bytes,
                file_count=v.file_count,
                package_sha256=v.package_sha256,
                created_at=v.created_at,
                published_at=v.published_at,
                validation=v.validation,
            )
            for v in versions
        ],
    )


def list_files(db: Session, name: str, version: int | None) -> list[FileEntry]:
    """列出指定版本包内的文件。"""
    skill = _require_skill(db, name)
    row = _require_version(db, skill, version)
    directory = storage.ensure_extracted(row.package_sha256, skill.name)
    return [FileEntry(**item) for item in storage.list_files(directory)]


def read_file(db: Session, name: str, path: str, version: int | None) -> str:
    """读取包内单个文本文件，用于预览。"""
    skill = _require_skill(db, name)
    row = _require_version(db, skill, version)
    directory = storage.ensure_extracted(row.package_sha256, skill.name)
    return storage.read_text(directory, path)


def download(db: Session, name: str, version: int | None) -> tuple[str, bytes]:
    """打包并返回指定版本内容，供浏览器或客户端下载。"""
    skill = _require_skill(db, name)
    row = _require_version(db, skill, version)
    directory = storage.ensure_extracted(row.package_sha256, skill.name)
    filename = f"{skill.name}-v{row.version}.zip"
    return filename, storage.build_zip(directory, skill.name)


def _comment_out(row: SkillComment) -> CommentOut:
    """把评论行转成出参，作者名取自冗余字段。"""
    return CommentOut(id=row.id, author=row.author_name, author_id=row.author_id, body=row.body, created_at=row.created_at)


def list_comments(db: Session, name: str, page: int, size: int) -> tuple[list[CommentOut], int]:
    """读取某技能的评论，游客可访问。

    调用时机：详情页打开评论弹层与加载更多时。
    """
    skill = _require_skill(db, name)
    rows, total = repository.list_comments(db, skill.id, (page - 1) * size, size)
    return [_comment_out(row) for row in rows], total


def add_comment(db: Session, name: str, payload: CommentCreate, actor: User) -> CommentOut:
    """发表评论。

    调用时机：登录用户在评论弹层点击发表时；正文长度由入参模型限制。
    """
    skill = _require_skill(db, name)
    comment = SkillComment(
        skill_id=skill.id,
        author_id=actor.id,
        author_name=actor.username,
        body=payload.body,
    )
    repository.create_comment(db, comment)
    return _comment_out(comment)


def delete_comment(db: Session, name: str, comment_id: Any, actor: User) -> None:
    """删除评论，作者本人或管理员可删。

    调用时机：评论弹层点击删除并确认后。
    """
    skill = _require_skill(db, name)
    comment = repository.get_comment(db, comment_id)
    if comment is None or comment.skill_id != skill.id:
        raise AppError("COMMENT_NOT_FOUND", "评论不存在", 404)
    if actor.role != "admin" and (comment.author_id is None or str(comment.author_id) != str(actor.id)):
        raise AppError("FORBIDDEN", "只能删除自己发表的评论", 403)
    repository.delete_comment(db, comment)


def _build_manifest_summary(manifest: dict[str, Any], fallback: str) -> str:
    """从 frontmatter 中取描述作为列表摘要。"""
    description = str(manifest.get("description", "")).strip()
    return description or fallback


def upload_new(db: Session, content: bytes, changelog: str, actor: User) -> UploadResult:
    """上传全新技能。

    调用时机：POST /api/skills 收到 zip 后；校验不通过时不会写入任何文件。
    """
    report = validate_package(content)
    ensure_valid(report)
    if repository.get_by_name(db, report.name) is not None:
        raise AppError("SKILL_EXISTS", "同名技能已存在，请改用上传新版本", 409)

    digest = storage.compute_digest(content)
    storage.save_package(content, digest)

    skill = Skill(
        name=report.name,
        display_name=str(report.manifest.get("title", "")).strip(),
        summary=_build_manifest_summary(report.manifest, report.description),
        created_by=actor.id,
    )
    repository.create_skill(db, skill)

    version = SkillVersion(
        skill_id=skill.id,
        version=1,
        package_sha256=digest,
        size_bytes=len(content),
        file_count=len(report.files),
        manifest=report.manifest,
        validation=report.as_dict(),
        changelog=changelog,
        status="draft",
        created_by=actor.id,
    )
    repository.create_version(db, version)
    record(db, actor, "upload", skill=skill, version=1, detail={"sha256": digest, "size": len(content)})

    return UploadResult(
        name=skill.name,
        version=version.version,
        status=version.status,
        warnings=report.warnings,
    )


def upload_version(db: Session, name: str, content: bytes, changelog: str, actor: User) -> UploadResult:
    """为既有技能上传新版本。"""
    skill = _require_skill(db, name)
    _require_manager(skill, actor)
    report = validate_package(content, expected_name=skill.name)
    ensure_valid(report)

    digest = storage.compute_digest(content)
    storage.save_package(content, digest)
    duplicate = repository.find_same_digest(db, skill.id, digest)

    version = SkillVersion(
        skill_id=skill.id,
        version=repository.next_version_number(db, skill.id),
        package_sha256=digest,
        size_bytes=len(content),
        file_count=len(report.files),
        manifest=report.manifest,
        validation=report.as_dict(),
        changelog=changelog,
        status="draft",
        created_by=actor.id,
    )
    repository.create_version(db, version)
    record(
        db,
        actor,
        "upload",
        skill=skill,
        version=version.version,
        detail={"sha256": digest, "size": len(content), "duplicate_of": duplicate.version if duplicate else None},
    )

    warnings = list(report.warnings)
    if duplicate is not None:
        warnings.append({"field": "package", "message": f"内容与 v{duplicate.version} 完全相同"})

    return UploadResult(
        name=skill.name,
        version=version.version,
        status=version.status,
        warnings=warnings,
        duplicate_of=duplicate.version if duplicate else None,
    )


def publish(db: Session, name: str, version: int, actor: User) -> SkillVersion:
    """发布指定版本并设为当前版本。

    调用时机：发布接口与设为当前；已发布版本内容不变，改指针只是切换线上版本。
    """
    skill = _require_skill(db, name)
    _require_manager(skill, actor)
    row = _require_version(db, skill, version)

    row.status = "published"
    row.published_at = _now()
    row.published_by = actor.id
    skill.current_version_id = row.id
    skill.summary = _build_manifest_summary(row.manifest, skill.summary)
    skill.updated_at = _now()

    record(db, actor, "publish", skill=skill, version=row.version, detail={"sha256": row.package_sha256})
    return row


def deprecate(db: Session, name: str, version: int, actor: User) -> SkillVersion:
    """废弃指定版本，若为当前版本则同时清空指针。"""
    skill = _require_skill(db, name)
    _require_manager(skill, actor)
    row = _require_version(db, skill, version)
    row.status = "deprecated"
    if skill.current_version_id == row.id:
        skill.current_version_id = None
    skill.updated_at = _now()
    record(db, actor, "deprecate", skill=skill, version=row.version, detail={})
    return row


def restore(db: Session, name: str, version: int, actor: User) -> SkillVersion:
    """把已废弃版本恢复为历史版本。

    调用时机：在「废弃」分组点击恢复；只改状态，不设为当前版本。
    """
    skill = _require_skill(db, name)
    _require_manager(skill, actor)
    row = _require_version(db, skill, version)
    if row.status != "deprecated":
        raise AppError("VERSION_NOT_DEPRECATED", "只有已废弃的版本可以恢复", 409)
    row.status = "published"
    skill.updated_at = _now()
    record(db, actor, "restore", skill=skill, version=row.version, detail={})
    return row


def delete_version(db: Session, name: str, version: int, actor: User) -> None:
    """物理删除单个已废弃版本。

    调用时机：创建者在「废弃」分组点击删除。
    当前版本不可删除；包体按摘要共享，仅当无其他版本引用时才清理磁盘文件。
    """
    from sqlalchemy import select

    from app.modules.skill.models import SkillVersion

    skill = _require_skill(db, name)
    _require_manager(skill, actor)
    row = _require_version(db, skill, version)
    if row.status != "deprecated":
        raise AppError("VERSION_NOT_DEPRECATED", "只有已废弃的版本可以删除", 409)
    if skill.current_version_id == row.id:
        raise AppError("VERSION_IS_CURRENT", "当前版本不能删除，请先把其他版本设为当前", 409)

    digest = row.package_sha256
    record(db, actor, "version_delete", skill=skill, version=row.version, detail={"sha256": digest})
    db.delete(row)
    db.flush()

    still_used = db.scalar(select(SkillVersion.id).where(SkillVersion.package_sha256 == digest).limit(1))
    if still_used is None:
        storage.remove_package(digest)



def delete_skill(db: Session, name: str, actor: User) -> None:
    """彻底删除技能与其所有版本。

    调用时机：技能创建者在详情页确认删除时；只有创建者本人可以删除。
    包体按摘要共享，仅当没有任何版本再引用时才删除磁盘文件。
    """
    from sqlalchemy import select

    from app.modules.skill.models import SkillVersion

    skill = _require_skill(db, name)
    _require_manager(skill, actor)

    versions = repository.list_versions(db, skill.id)
    digests = {version.package_sha256 for version in versions}

    record(
        db,
        actor,
        "delete",
        skill=skill,
        detail={"version_count": len(versions), "versions": [v.version for v in versions]},
    )

    # 先断开 current_version 外键，否则删除版本行会被约束拦住
    skill.current_version_id = None
    db.flush()

    for version in versions:
        db.delete(version)
    db.delete(skill)
    db.flush()

    for digest in digests:
        still_used = db.scalar(select(SkillVersion.id).where(SkillVersion.package_sha256 == digest).limit(1))
        if still_used is None:
            storage.remove_package(digest)


def stats(db: Session) -> dict[str, int]:
    """概览页统计数据。"""
    return {
        "skill_count": repository.count_skills(db),
        "version_count": repository.count_versions(db),
        "published_count": len(repository.published_skills(db)),
    }


def published_index(db: Session) -> list[dict[str, Any]]:
    """生成机器可读索引，供客户端与安装器发现技能。"""
    skills = repository.published_skills(db)
    currents = repository.current_versions(db, skills)
    items: list[dict[str, Any]] = []
    for skill in skills:
        version = currents.get(skill.current_version_id) if skill.current_version_id else None
        if version is None:
            continue
        items.append(
            {
                "name": skill.name,
                "description": skill.summary,
                "latestVersion": version.version,
                "sha256": version.package_sha256,
                "size": version.size_bytes,
                "downloadUrl": f"/api/skills/{skill.name}/download?version={version.version}",
                "updatedAt": (version.published_at or skill.updated_at).isoformat(),
            }
        )
    return items

def transfer_owner(db: Session, name: str, username: str, actor: User) -> Skill:
    """把技能归属转给另一个账号。

    调用时机：管理员在详情页执行「转移归属」；仅管理员可用。
    """
    from app.modules.auth.repository import get_by_username

    skill = _require_skill(db, name)
    if actor.role != "admin":
        raise AppError("FORBIDDEN", "只有管理员可以转移归属", 403)
    target = get_by_username(db, username)
    if target is None:
        raise AppError("USER_NOT_FOUND", "目标账号不存在", 404)
    if not target.enabled:
        raise AppError("USER_DISABLED", "目标账号已停用，不能接收技能", 409)
    if skill.created_by is not None and str(skill.created_by) == str(target.id):
        return skill

    skill.created_by = target.id
    skill.updated_at = _now()
    record(db, actor, "transfer", skill=skill, detail={"to": target.username})
    return skill
