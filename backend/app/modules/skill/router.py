"""技能接口。

调用时机：前端的列表、详情、上传、发布与下载，以及客户端获取技能索引。
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, ok
from app.core.security import get_current_user, require_admin
from app.db.session import get_db
from app.modules.audit import service as audit_service
from app.modules.auth.models import User
from app.modules.skill import service
from app.modules.skill.schemas import CommentCreate, TransferOwnerRequest, VersionOut

router = APIRouter(tags=["技能"])


def _read_upload(upload: UploadFile) -> bytes:
    """读取上传文件并执行体积上限检查。

    调用时机：接收 zip 后立即调用，超限直接拒绝，避免读入内存。
    """
    settings = get_settings()
    content = upload.file.read(settings.max_package_bytes + 1)
    if len(content) > settings.max_package_bytes:
        raise AppError("PACKAGE_TOO_LARGE", f"包体积超过 {settings.max_package_bytes // (1024 * 1024)} MB", 413)
    if not content:
        raise AppError("PACKAGE_EMPTY", "上传内容为空", 400)
    return content


@router.get("/api/skills")
def list_skills(
    q: str | None = Query(None, max_length=64),
    status: str | None = Query(None, pattern=r"^(active|archived)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    """分页查询技能。"""
    items, total = service.list_skills(db, q=q, status=status, page=page, size=size)
    return ok({"items": [item.model_dump(mode="json") for item in items], "total": total, "page": page, "size": size})


@router.get("/api/skills/{name}")
def get_skill(name: str, db: Session = Depends(get_db)) -> dict:
    """查询技能详情与版本列表。"""
    detail = service.get_detail(db, name)
    return ok(detail.model_dump(mode="json"))


@router.get("/api/skills/{name}/files")
def list_files(
    name: str,
    version: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
) -> dict:
    """列出包内文件，供文件树使用。"""
    files = service.list_files(db, name, version)
    return ok([item.model_dump(mode="json") for item in files])


@router.get("/api/skills/{name}/file")
def read_file(
    name: str,
    path: str = Query(..., min_length=1, max_length=512),
    version: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
) -> dict:
    """读取单个文件内容，用于在线预览。"""
    text = service.read_file(db, name, path, version)
    return ok({"path": path, "content": text})


@router.post("/api/skills")
def create_skill(
    file: UploadFile = File(...),
    changelog: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """上传全新技能，校验通过后创建 v1 草稿。"""
    result = service.upload_new(db, _read_upload(file), changelog, user)
    db.commit()
    return ok(result.model_dump(mode="json"))


@router.post("/api/skills/{name}/versions")
def create_version(
    name: str,
    file: UploadFile = File(...),
    changelog: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """为既有技能上传新版本。"""
    result = service.upload_version(db, name, _read_upload(file), changelog, user)
    db.commit()
    return ok(result.model_dump(mode="json"))


@router.post("/api/skills/{name}/versions/{version}/publish")
def publish_version(
    name: str,
    version: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """发布指定版本并设为当前版本。"""
    row = service.publish(db, name, version, user)
    db.commit()
    return ok(VersionOut.model_validate(row, from_attributes=True).model_dump(mode="json"))


@router.post("/api/skills/{name}/versions/{version}/deprecate")
def deprecate_version(
    name: str,
    version: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """废弃指定版本。"""
    row = service.deprecate(db, name, version, user)
    db.commit()
    return ok({"version": row.version, "status": row.status})


@router.post("/api/skills/{name}/versions/{version}/restore")
def restore_version(
    name: str,
    version: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """把已废弃版本恢复为历史版本。"""
    row = service.restore(db, name, version, user)
    db.commit()
    return ok({"version": row.version, "status": row.status})


@router.delete("/api/skills/{name}/versions/{version}")
def delete_version(
    name: str,
    version: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """物理删除单个已废弃版本，仅创建者可用。"""
    service.delete_version(db, name, version, user)
    db.commit()
    return ok({"version": version, "deleted": True})


@router.patch("/api/skills/{name}/owner")
def transfer_owner(
    name: str,
    payload: TransferOwnerRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    """把技能归属转给指定账号，仅管理员可用。"""
    skill = service.transfer_owner(db, name, payload.username, user)
    db.commit()
    return ok({"name": skill.name, "created_by": str(skill.created_by)})


@router.delete("/api/skills/{name}")
def delete_skill(
    name: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """彻底删除技能与所有版本，仅创建者可用。"""
    service.delete_skill(db, name, user)
    db.commit()
    return ok({"name": name, "deleted": True})


@router.get("/api/skills/{name}/comments")
def list_comments(
    name: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    """分页读取技能评论，游客可访问。"""
    items, total = service.list_comments(db, name, page, size)
    return ok({"items": [item.model_dump(mode="json") for item in items], "total": total, "page": page, "size": size})


@router.post("/api/skills/{name}/comments")
def create_comment(
    name: str,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """发表评论，需要登录。"""
    comment = service.add_comment(db, name, payload, user)
    db.commit()
    return ok(comment.model_dump(mode="json"))


@router.delete("/api/skills/{name}/comments/{comment_id}")
def delete_comment(
    name: str,
    comment_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """删除评论，作者本人或管理员可用。"""
    service.delete_comment(db, name, comment_id, user)
    db.commit()
    return ok({"deleted": True})


@router.get("/api/skills/{name}/download")
def download_skill(
    name: str,
    version: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
) -> Response:
    """下载指定版本 zip，未指定版本时取当前发布版本。"""
    filename, payload = service.download(db, name, version)
    return Response(
        content=payload,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/stats")
def get_stats(db: Session = Depends(get_db)) -> dict:
    """返回概览统计与最近操作。"""
    data = service.stats(db)
    data["recent"] = [
        {
            "action": row.action,
            "actor": row.actor_name,
            "skill": row.skill_name,
            "version": row.version,
            "at": row.created_at.isoformat(),
        }
        for row in audit_service.recent(db)
    ]
    return ok(data)


@router.get("/.well-known/skills.json")
def skills_index(db: Session = Depends(get_db)) -> dict:
    """机器可读的技能索引，供客户端与安装器发现已发布技能。"""
    return {"skills": service.published_index(db)}
