"""技能包校验的单元测试。

调用时机：本地开发与 CI 执行 pytest 时运行，不依赖数据库。
"""

from __future__ import annotations

import io
import zipfile

from app.modules.package.validator import validate_package


def make_zip(files: dict[str, str | bytes]) -> bytes:
    """按给定文件字典构造 zip 字节流。"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def skill_md(name: str = "demo-skill", description: str = "演示技能", body: str = "# 说明\n") -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n{body}"


def test_valid_package_with_root_directory() -> None:
    content = make_zip({"demo-skill/SKILL.md": skill_md(), "demo-skill/references/a.md": "# a"})
    report = validate_package(content)
    assert report.errors == []
    assert report.name == "demo-skill"
    assert {item["path"] for item in report.files} == {"SKILL.md", "references/a.md"}


def test_valid_package_without_root_directory() -> None:
    content = make_zip({"SKILL.md": skill_md(name="flat-skill")})
    report = validate_package(content)
    assert report.errors == []
    assert report.name == "flat-skill"


def test_missing_skill_md() -> None:
    report = validate_package(make_zip({"demo-skill/readme.md": "hi"}))
    assert any(item["field"] == "SKILL.md" for item in report.errors)


def test_invalid_name() -> None:
    content = make_zip({"Bad_Name/SKILL.md": skill_md(name="Bad_Name")})
    report = validate_package(content)
    assert any(item["field"] == "name" for item in report.errors)


def test_name_must_match_directory() -> None:
    content = make_zip({"demo-skill/SKILL.md": skill_md(name="other-skill")})
    report = validate_package(content)
    assert any(item["field"] == "name" for item in report.errors)


def test_path_traversal_rejected() -> None:
    content = make_zip({"demo-skill/SKILL.md": skill_md(), "../evil.txt": "x"})
    report = validate_package(content)
    assert any(item["field"] == "path" for item in report.errors)


def test_expected_name_mismatch() -> None:
    content = make_zip({"demo-skill/SKILL.md": skill_md()})
    report = validate_package(content, expected_name="another-skill")
    assert any(item["field"] == "name" for item in report.errors)


def test_description_too_long() -> None:
    content = make_zip({"demo-skill/SKILL.md": skill_md(description="x" * 1025)})
    report = validate_package(content)
    assert any(item["field"] == "description" for item in report.errors)


def test_scripts_and_missing_reference_produce_warnings() -> None:
    body = "# 说明\n参见 [参考](references/missing.md)\n"
    content = make_zip(
        {
            "demo-skill/SKILL.md": skill_md(body=body),
            "demo-skill/scripts/run.py": "print('hi')",
        }
    )
    report = validate_package(content)
    assert report.errors == []
    fields = {item["field"] for item in report.warnings}
    assert "scripts" in fields
    assert "references" in fields


def test_not_a_zip() -> None:
    report = validate_package(b"not a zip file")
    assert any(item["field"] == "package" for item in report.errors)


def test_utf8_bom_is_tolerated() -> None:
    content = make_zip({"demo-skill/SKILL.md": "\ufeff" + skill_md()})
    report = validate_package(content)
    assert report.errors == []
    assert report.name == "demo-skill"


def test_windows_backslash_paths_are_accepted() -> None:
    """Windows 资源管理器压缩的包用反斜杠分隔，应当照常通过。"""
    content = make_zip(
        {
            "demo-skill\\SKILL.md": skill_md(),
            "demo-skill\\references\\a.md": "# a",
            "demo-skill\\scripts\\run.py": "print('hi')",
        }
    )
    report = validate_package(content)
    assert report.errors == []
    assert report.name == "demo-skill"
    assert {item["path"] for item in report.files} == {"SKILL.md", "references/a.md", "scripts/run.py"}


def test_windows_directory_entries_are_skipped() -> None:
    """Windows 压缩包里的目录条目以反斜杠结尾，不能当成文件校验。"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("demo-skill\\SKILL.md", skill_md())
        archive.writestr("demo-skill\\verify\\", "")
    report = validate_package(buffer.getvalue())
    assert report.errors == []
    assert report.name == "demo-skill"
