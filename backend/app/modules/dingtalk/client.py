"""钉钉开放平台客户端。

调用时机：扫码登录换取身份，以及登录时同步企业管理员角色。
只依赖 httpx，不引入官方 SDK。
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import get_settings
from app.core.errors import AppError

_TIMEOUT = 10.0
_TOKEN_TTL_MARGIN = 60
_ROLE_CACHE_SECONDS = 300

_token_cache: dict[str, Any] = {"value": "", "expires_at": 0.0}
_admin_cache: dict[str, Any] = {"value": [], "expires_at": 0.0}


@dataclass
class DingTalkProfile:
    """扫码登录换回的用户身份。"""

    union_id: str
    user_id: str
    name: str
    active: bool = True


def _fail(message: str) -> AppError:
    return AppError("DINGTALK_ERROR", message, 502)


def _request(method: str, url: str, payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    """发一个 JSON 请求并解析响应，网络与状态码错误统一转成 502。"""
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            response = client.request(method, url, json=payload, headers=headers or {})
            body: Any = response.json()
    except Exception as exc:  # noqa: BLE001 - 网络异常统一转成业务错误
        raise _fail(f"调用钉钉接口失败：{exc}") from exc
    if response.status_code != 200:
        raise _fail(f"调用钉钉接口失败：HTTP {response.status_code} {str(body)[:200]}")
    if not isinstance(body, dict):
        raise _fail("钉钉接口返回格式异常")
    return body


def app_token() -> str:
    """取企业应用 access_token，带进程内缓存。

    走旧版 oapi/gettoken：新版 /v1.0/oauth2/accessToken 对部分应用会返回
    invalidClientIdOrSecret，而 gettoken 使用同一对 AppKey/AppSecret 可以正常换取。
    """
    now = time.time()
    if _token_cache["value"] and _token_cache["expires_at"] > now + _TOKEN_TTL_MARGIN:
        return str(_token_cache["value"])
    settings = get_settings()
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            response = client.get(
                f"{settings.dingtalk_oapi_base}/gettoken",
                params={"appkey": settings.dingtalk_client_id, "appsecret": settings.dingtalk_client_secret},
            )
            body: Any = response.json()
    except Exception as exc:  # noqa: BLE001
        raise _fail(f"获取钉钉应用凭证失败：{exc}") from exc
    if response.status_code != 200 or body.get("errcode"):
        raise _fail(f"获取钉钉应用凭证失败：{str(body)[:200]}")
    token = str(body.get("access_token") or "")
    if not token:
        raise _fail("获取钉钉应用凭证失败：响应里没有 access_token")
    _token_cache["value"] = token
    _token_cache["expires_at"] = now + int(body.get("expires_in") or 7200)
    return token


def exchange_code(auth_code: str) -> DingTalkProfile:
    """用扫码得到的 authCode 换用户身份。

    链路：authCode → 用户 accessToken → /contact/users/me 拿 unionId → 换企业内 userId → 读详情。
    """
    settings = get_settings()
    token_body = _request(
        "POST",
        f"{settings.dingtalk_api_base}/v1.0/oauth2/userAccessToken",
        {
            "clientId": settings.dingtalk_client_id,
            "clientSecret": settings.dingtalk_client_secret,
            "code": auth_code,
            "grantType": "authorization_code",
        },
    )
    user_token = str(token_body.get("accessToken") or "")
    if not user_token:
        raise _fail(f"换取用户凭证失败：{str(token_body)[:200]}")

    me = _request(
        "GET",
        f"{settings.dingtalk_api_base}/v1.0/contact/users/me",
        headers={"x-acs-dingtalk-access-token": user_token},
    )
    union_id = str(me.get("unionId") or "")
    if not union_id:
        raise _fail("未获取到 unionId，请确认应用已开通通讯录读权限")
    name = str(me.get("nick") or "")

    user_id = user_id_by_union_id(union_id)
    profile = DingTalkProfile(union_id=union_id, user_id=user_id, name=name)
    detail = user_detail(user_id)
    if detail:
        profile.name = str(detail.get("name") or name)
        profile.active = bool(detail.get("active", True))
    return profile


def user_id_by_union_id(union_id: str) -> str:
    """unionId 换企业内 userId；非本企业成员会失败。"""
    settings = get_settings()
    body = _request(
        "POST",
        f"{settings.dingtalk_oapi_base}/topapi/user/getbyunionid?access_token={quote(app_token())}",
        {"unionid": union_id},
    )
    if body.get("errcode"):
        raise _fail("该钉钉账号不属于本公司或不在应用可见范围内，无法登录")
    user_id = str((body.get("result") or {}).get("userid") or "")
    if not user_id:
        raise _fail("无法解析钉钉用户 ID")
    return user_id


def user_detail(user_id: str) -> dict[str, Any]:
    """读取用户详情，失败时返回空字典（不影响登录）。"""
    settings = get_settings()
    try:
        body = _request(
            "POST",
            f"{settings.dingtalk_oapi_base}/topapi/v2/user/get?access_token={quote(app_token())}",
            {"userid": user_id, "language": "zh_CN"},
        )
    except AppError:
        return {}
    if body.get("errcode"):
        return {}
    return body.get("result") or {}


def list_admin_ids() -> set[str]:
    """取企业管理员 userId 集合（主管理员与子管理员），缓存 5 分钟。"""
    now = time.time()
    if _admin_cache["expires_at"] > now:
        return set(_admin_cache["value"])
    settings = get_settings()
    body = _request(
        "POST",
        f"{settings.dingtalk_oapi_base}/topapi/user/listadmin?access_token={quote(app_token())}",
        {},
    )
    errcode = int(body.get("errcode") or 0)
    if errcode == 43007:
        raise _fail("钉钉管理员列表无权限：请在开发者后台给应用勾选「成员信息读权限」")
    if errcode:
        raise _fail(f"读取钉钉管理员列表失败：{body.get('errmsg') or errcode}")
    ids = {
        str(item.get("userid"))
        for item in (body.get("result") or [])
        if item.get("userid") and int(item.get("sys_level") or 0) > 0
    }
    _admin_cache["value"] = ids
    _admin_cache["expires_at"] = now + _ROLE_CACHE_SECONDS
    return ids
