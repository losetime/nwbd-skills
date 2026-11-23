"""账号相关请求与响应模型。

调用时机：扫码登录、当前用户与用户管理接口的入参校验与出参序列化。
"""

from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel, Field


class DingTalkExchangeRequest(BaseModel):
    """前端扫码后回传的授权码。"""

    auth_code: str = Field(min_length=1, max_length=512)


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    display_name: str
    role: str
    enabled: bool
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserUpdateRequest(BaseModel):
    role: str | None = Field(default=None, pattern=r"^(member|admin)$")
    enabled: bool | None = None
