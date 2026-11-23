"""技能包校验。

调用时机：上传新技能或新版本时，在落盘之前对 zip 内容执行全部检查。
校验只读内存中的数据，失败时不产生任何磁盘文件。
"""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass, field
from typing import Any

import yaml

from app.core.config import get_settings
from app.core.errors import AppError

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_PATTERN = re.compile(r"\]\(([^)\s]+)\)")
# 允许的 frontmatter 键，其余键保留但不校验
ALLOWED_LINK_PREFIXES = ("http://", "https://", "#", "mailto:")


@dataclass
class ValidationReport:
    """校验结果。

    errors 为阻断项，非空时本次上传失败；warnings 仅提示，不阻断。
    """

    name: str = ""
    description: str = ""
    manifest: dict[str, Any] = field(default_factory=dict)
    files: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    warnings: list[dict[str, str]] = field(default_factory=list)

    def add_error(self, field_name: str, message: str) -> None:
        self.errors.append({"field": field_name, "message": message})

    def add_warning(self, field_name: str, message: str) -> None:
        self.warnings.append({"field": field_name, "message": message})

    def as_dict(self) -> dict[str, Any]:
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "manifest": self.manifest,
            "files": self.files,
        }


def _entry_name(info: zipfile.ZipInfo) -> str:
    """统一 zip 内路径分隔符。

    调用时机：读取每个条目时；Windows 资源管理器等工具会把反斜杠写进 zip，
    而 zip 规范要求正斜杠，这里统一归一化后再校验与落盘。
    """
    return info.filename.replace("\\", "/")


def _is_safe_entry(name: str) -> bool:
    """判断压缩包内路径是否安全，拒绝绝对路径、上跳与盘符。"""
    if not name or name.startswith("/") or "\\" in name:
        return False
    if re.match(r"^[a-zA-Z]:", name):
        return False
    parts = name.split("/")
    return all(part not in ("", ".", "..") for part in parts)


def _split_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    """拆分 YAML frontmatter 与正文，解析失败返回 None。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), -1)
    if end < 0:
        return None, text
    try:
        data = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError:
        return None, text
    if not isinstance(data, dict):
        return None, text
    return data, "\n".join(lines[end + 1 :])


def validate_package(content: bytes, expected_name: str | None = None) -> ValidationReport:
    """执行完整的包校验。

    调用时机：接收上传文件后、写入存储前调用；返回值 errors 非空即拒绝。
    """
    settings = get_settings()
    report = ValidationReport()

    if len(content) > settings.max_package_bytes:
        report.add_error("package", f"包体积超过上限 {settings.max_package_bytes // (1024 * 1024)} MB")
        return report

    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile:
        report.add_error("package", "不是合法的 zip 文件")
        return report

    infos = [i for i in archive.infolist() if not i.is_dir()]
    if not infos:
        report.add_error("package", "压缩包内没有文件")
        return report
    if len(infos) > settings.max_entries:
        report.add_error("package", f"文件数量超过上限 {settings.max_entries}")

    total_size = 0
    for info in infos:
        entry = _entry_name(info)
        if not _is_safe_entry(entry):
            report.add_error("path", f"非法路径：{entry}")
            continue
        if info.file_size > settings.max_file_bytes:
            report.add_error("file", f"单文件超过 {settings.max_file_bytes // (1024 * 1024)} MB：{entry}")
        if info.compress_size > 0 and info.file_size / info.compress_size > settings.max_compression_ratio:
            report.add_error("package", f"压缩比异常，可能为压缩炸弹：{entry}")
        total_size += info.file_size

    if total_size > settings.max_package_bytes:
        report.add_error("package", "解压后体积超过上限")
    if report.errors:
        return report

    names = [_entry_name(i) for i in infos]
    root = ""
    if "SKILL.md" not in names:
        tops = {name.split("/")[0] for name in names}
        if len(tops) == 1:
            candidate = next(iter(tops))
            if f"{candidate}/SKILL.md" in names:
                root = candidate
    skill_md_path = f"{root}/SKILL.md" if root else "SKILL.md"
    if skill_md_path not in names:
        report.add_error("SKILL.md", "缺少 SKILL.md，且无法确定唯一根目录")
        return report

    try:
        raw_text = archive.read(skill_md_path).decode("utf-8")
    except UnicodeDecodeError:
        report.add_error("SKILL.md", "SKILL.md 不是 UTF-8 编码")
        return report

    # Windows 编辑器常写入 BOM，去掉后再解析 frontmatter
    raw_text = raw_text.lstrip("\ufeff")

    manifest, body = _split_frontmatter(raw_text)
    if manifest is None:
        report.add_error("frontmatter", "SKILL.md 缺少合法 YAML frontmatter（--- 包裹的元信息块）")
        return report

    report.manifest = {k: v for k, v in manifest.items() if isinstance(k, str)}
    name = str(manifest.get("name", "")).strip()
    description = str(manifest.get("description", "")).strip()

    if not name:
        report.add_error("name", "frontmatter 缺少 name")
    elif not NAME_PATTERN.match(name) or len(name) > 64:
        report.add_error("name", "name 只能包含小写字母、数字与连字符，长度 1-64")
    elif root and root != name:
        report.add_error("name", f"name（{name}）必须与包内根目录名（{root}）一致")

    if expected_name and name and name != expected_name:
        report.add_error("name", f"name（{name}）与目标技能（{expected_name}）不一致")

    if not description:
        report.add_error("description", "frontmatter 缺少 description")
    elif len(description) > 1024:
        report.add_error("description", "description 超过 1024 字符")

    if len(body.splitlines()) > 500:
        report.add_warning("SKILL.md", "正文超过 500 行，建议把细节拆到 references/ 目录")

    available = {name[len(root) + 1 :] if root else name for name in names}
    for target in LINK_PATTERN.findall(body):
        if target.startswith(ALLOWED_LINK_PREFIXES):
            continue
        cleaned = target.split("#", 1)[0].lstrip("./")
        if cleaned and cleaned not in available:
            report.add_warning("references", f"引用的文件不存在：{target}")

    if any(p.startswith(("scripts/", "bin/")) or p.endswith((".sh", ".py", ".js")) for p in available):
        report.add_warning("scripts", "包内含可执行脚本，发布前请确认来源可信")

    report.name = name
    report.description = description
    report.files = [
        {
            "path": name[len(root) + 1 :] if root else name,
            "size": info.file_size,
        }
        for info, name in zip(infos, names)
    ]
    return report


def ensure_valid(report: ValidationReport) -> None:
    """在校验失败时抛出携带明细的 AppError。"""
    if report.errors:
        raise AppError("PACKAGE_INVALID", "技能包校验未通过", 422, report.errors)
