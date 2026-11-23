"""技能包存储。

调用时机：校验通过后写入原始包与解压副本；读取文件树、预览与下载时按摘要访问。
包体按 sha256 内容寻址，同内容跨技能跨版本自动复用。
"""

from __future__ import annotations

import hashlib
import io
import shutil
import zipfile
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.errors import AppError


def compute_digest(content: bytes) -> str:
    """计算内容摘要，作为包体唯一标识。"""
    return hashlib.sha256(content).hexdigest()


def save_package(content: bytes, digest: str) -> Path:
    """写入原始包，已存在同摘要文件时直接复用。"""
    settings = get_settings()
    settings.ensure_dirs()
    target = settings.packages_dir / f"{digest}.zip"
    if not target.exists():
        temp = target.with_suffix(".zip.tmp")
        temp.write_bytes(content)
        temp.replace(target)
    return target


def _detect_root(names: list[str]) -> str | None:
    """判断包是否被单一顶层目录包裹。

    调用时机：解压前，用于剥掉 skill-name/ 这一层，使文件路径与技能根目录对齐。
    """
    tops = {name.split("/")[0] for name in names if name}
    if len(tops) != 1:
        return None
    top = next(iter(tops))
    if all("/" in name for name in names):
        return top
    return None


def _extract_root(zip_path: Path, expected_root: str | None) -> None:
    """解压到临时目录后整体改名，避免半成品目录被读取。"""
    settings = get_settings()
    final_dir = settings.extracted_dir / zip_path.stem
    if final_dir.exists():
        return
    temp_dir = settings.extracted_dir / f"{zip_path.stem}.tmp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as archive:
        entries = [info for info in archive.infolist() if not info.is_dir()]
        # Windows 压缩工具会写反斜杠，统一成正斜杠后再判断根目录与落盘路径
        names = [info.filename.replace("\\", "/") for info in entries]
        root = expected_root or _detect_root(names)
        for info, entry in zip(entries, names):
            parts = entry.split("/")
            if root and parts[0] == root:
                parts = parts[1:]
            if not parts:
                continue
            destination = (temp_dir / Path(*parts)).resolve()
            if not str(destination).startswith(str(temp_dir.resolve())):
                raise AppError("PACKAGE_INVALID", f"非法路径：{info.filename}", 422)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, open(destination, "wb") as target:
                shutil.copyfileobj(source, target)

    temp_dir.replace(final_dir)


def ensure_extracted(digest: str, root: str | None = None) -> Path:
    """确保解压副本存在并返回目录。

    调用时机：首次读取文件树、预览或下载前；后续命中已存在的副本直接返回。
    """
    settings = get_settings()
    zip_path = settings.packages_dir / f"{digest}.zip"
    if not zip_path.exists():
        raise AppError("PACKAGE_MISSING", "包体文件缺失", 500)
    _extract_root(zip_path, root)
    return settings.extracted_dir / digest


def list_files(directory: Path) -> list[dict[str, Any]]:
    """列出解压目录下的全部文件，路径相对根目录。"""
    files: list[dict[str, Any]] = []
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            files.append({"path": path.relative_to(directory).as_posix(), "size": path.stat().st_size})
    return files


def read_text(directory: Path, relative_path: str) -> str:
    """读取文本文件内容，拒绝越界路径与非文本内容。"""
    settings = get_settings()
    target = (directory / relative_path).resolve()
    if not str(target).startswith(str(directory.resolve())) or not target.is_file():
        raise AppError("FILE_NOT_FOUND", "文件不存在", 404)
    if target.stat().st_size > settings.max_text_preview_bytes:
        raise AppError("FILE_TOO_LARGE", "文件过大，无法在线预览", 413)
    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise AppError("FILE_NOT_TEXT", "该文件不是文本，无法预览", 415) from exc


def remove_package(digest: str) -> None:
    """删除某个摘要对应的包体与解压副本。

    调用时机：技能被彻底删除，且确认已无任何版本引用该摘要之后。
    """
    settings = get_settings()
    package = settings.packages_dir / f"{digest}.zip"
    if package.exists():
        package.unlink()
    extracted = settings.extracted_dir / digest
    if extracted.exists():
        shutil.rmtree(extracted, ignore_errors=True)


def build_zip(directory: Path, root_name: str) -> bytes:
    """按技能目录结构重新打包，用于下载。"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                archive.write(path, f"{root_name}/{path.relative_to(directory).as_posix()}")
    return buffer.getvalue()
