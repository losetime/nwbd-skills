"""技能相关请求与响应模型。

调用时机：列表、详情、版本与文件接口的出参序列化。
"""

from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel, Field, field_validator


class SkillListItem(BaseModel):
    name: str
    display_name: str
    summary: str
    status: str
    version_count: int
    current_version: int | None
    file_count: int
    size_bytes: int
    owner: str = ""
    updated_at: dt.datetime


class VersionOut(BaseModel):
    version: int
    status: str
    changelog: str
    size_bytes: int
    file_count: int
    package_sha256: str
    created_at: dt.datetime
    published_at: dt.datetime | None
    validation: dict


class SkillDetail(BaseModel):
    name: str
    display_name: str
    summary: str
    status: str
    current_version: int | None
    created_by: uuid.UUID | None = None
    owner: str = ""
    created_at: dt.datetime
    updated_at: dt.datetime
    versions: list[VersionOut]


class FileEntry(BaseModel):
    path: str
    size: int


class UploadResult(BaseModel):
    name: str
    version: int
    status: str
    warnings: list[dict[str, str]]
    duplicate_of: int | None = None

class TransferOwnerRequest(BaseModel):
    username: str


class CommentCreate(BaseModel):
    """发表评论的入参：去空格后不超过 500 字。"""

    body: str = Field(min_length=1, max_length=500)

    @field_validator("body")
    @classmethod
    def strip_body(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("评论不能为空")
        return text


class CommentOut(BaseModel):
    id: uuid.UUID
    author: str
    author_id: uuid.UUID | None
    body: str
    created_at: dt.datetime
