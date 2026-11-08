#!/usr/bin/env python3
"""Emit a read-only LGF/GASP/Mover workspace manifest as JSON.
Controlled input/encoding errors normally exit 2. Output-I/O errors are failures,
but interpreter shutdown flushing can replace that code (e.g. CPython 120).
Do not treat a partial stream or a nonzero exit as a successful manifest.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


INTERESTING_PLUGINS = {
    "AnimationLocomotionLibrary",
    "AnimationWarping",
    "Chooser",
    "GameplayAbilities",
    "IKRig",
    "MotionWarping",
    "Mover",
    "NetworkPrediction",
    "PoseSearch",
}

LGF_DOCUMENT_NAMES = (
    "README.md",
    "LGameplayFramework_Tutorial.md",
    "LGameplayFramework_API.md",
)


def load_json(path: Path) -> dict[str, Any]:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"JSON 对象内重复键：{key!r}")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)
    except (RecursionError, MemoryError) as exc:
        raise ValueError(f"无法读取 JSON：{path}: 超出解析资源限制 ({type(exc).__name__})") from exc
    except (OSError, UnicodeError, ValueError) as exc:
        raise ValueError(f"无法读取 JSON：{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON 根对象不是对象：{path}")
    return value


def display_path(root: Path, path: Path) -> str:
    """Return a project-relative path, or an absolute path for external links."""
    absolute = path.absolute()
    try:
        return absolute.relative_to(root).as_posix()
    except ValueError:
        return str(absolute)


def descriptor_modules(data: dict[str, Any], path: Path) -> list[str]:
    modules = data.get("Modules", [])
    if not isinstance(modules, list):
        raise ValueError(f"{path}: $.Modules 必须为数组，不能为 null 或其他类型")
    names: list[str] = []
    first_index: dict[str, int] = {}
    for index, entry in enumerate(modules):
        location = f"$.Modules[{index}]"
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: {location} 必须为对象")
        name = entry.get("Name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{path}: {location}.Name 必须为非空字符串")
        if name in first_index:
            raise ValueError(
                f"{path}: {location}.Name 重复模块名 {name!r}；"
                f"首次声明位于 $.Modules[{first_index[name]}].Name"
            )
        first_index[name] = index
        names.append(name)
    return names


def display_paths(root: Path, paths: list[Path]) -> list[str]:
    return sorted(display_path(root, path) for path in paths)


def find_single_project(root: Path) -> Path:
    projects = sorted(path for path in root.glob("*.uproject") if path.is_file())
    if len(projects) != 1:
        names = ", ".join(path.name for path in projects) or "无"
        raise ValueError(f"项目根目录必须恰好包含一个 .uproject；当前：{names}")
    return projects[0]


def find_lgf_plugin(root: Path) -> Path | None:
    matches = sorted(
        path.absolute()
        for path in root.glob("Plugins/**/LGameplayFramework.uplugin")
        if path.is_file()
    )
    if len(matches) > 1:
        candidates = ", ".join(display_path(root, path) for path in matches)
        raise ValueError(f"发现多个 LGameplayFramework 插件副本，无法确定真实源码：{candidates}")
    return matches[0] if matches else None


def collect_build_files(root: Path, lgf_plugin: Path | None) -> tuple[list[Path], list[Path]]:
    project_files = (
        sorted(path.absolute() for path in (root / "Source").glob("**/*.Build.cs") if path.is_file())
        if (root / "Source").is_dir()
        else []
    )
    plugin_files: list[Path] = []
    if lgf_plugin is not None:
        plugin_source = lgf_plugin.parent / "Source"
        if plugin_source.is_dir():
            plugin_files = sorted(path.absolute() for path in plugin_source.glob("**/*.Build.cs") if path.is_file())
    return project_files, plugin_files


def plugin_summary(project_data: dict[str, Any], path: Path | None = None) -> dict[str, bool | None]:
    """Read explicit project declarations, not effective runtime plugin state."""
    result: dict[str, bool | None] = {}
    plugins = project_data.get("Plugins", [])
    source = path or ".uproject"
    if not isinstance(plugins, list):
        raise ValueError(f"{source}: Plugins 必须为数组")
    seen: set[str] = set()
    for index, entry in enumerate(plugins):
        if not isinstance(entry, dict):
            raise ValueError(f"{source}: Plugins[{index}] 必须为对象")
        name = entry.get("Name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{source}: Plugins[{index}].Name 必须为非空字符串")
        if name in seen:
            raise ValueError(f"{source}: Plugins 中存在重复插件声明 conflict：{name}")
        seen.add(name)
        enabled = entry.get("Enabled")
        if "Enabled" in entry and type(enabled) is not bool:
            raise ValueError(f"{source}: Plugins[{index}].Enabled 必须为布尔值")
        if name in INTERESTING_PLUGINS:
            result[name] = enabled
    return dict(sorted(result.items()))


def inspect_engine(engine_root: Path | None) -> dict[str, Any]:
    if engine_root is None:
        return {
            "status": "not_provided",
            "verified": False,
            "root": None,
            "build_version": None,
            "mover": None,
        }

    root = engine_root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"引擎根目录不存在：{root}")

    build_version_path = root / "Engine" / "Build" / "Build.version"
    if not build_version_path.is_file():
        raise ValueError(f"引擎缺少 Build.version：{build_version_path}")
    build_data = load_json(build_version_path)

    version_keys = ("MajorVersion", "MinorVersion", "PatchVersion")
    for key in version_keys:
        value = build_data.get(key)
        if type(value) is not int or value < 0:
            raise ValueError(f"{build_version_path}: {key} 必须为非负整数（不接受布尔值）")

    plugins_root = root / "Engine" / "Plugins"
    mover_descriptors = sorted(
        path.resolve()
        for path in plugins_root.glob("**/Mover.uplugin")
        if path.is_file()
    ) if plugins_root.is_dir() else []
    if len(mover_descriptors) > 1:
        candidates = ", ".join(str(path) for path in mover_descriptors)
        raise ValueError(f"引擎中发现多个 Mover.uplugin，无法确定真实插件：{candidates}")
    mover_descriptor = mover_descriptors[0] if mover_descriptors else None
    mover_root = mover_descriptor.parent if mover_descriptor is not None else None

    return {
        "status": "verified",
        "verified": True,
        "root": str(root),
        "build_version_file": str(build_version_path),
        "build_version": {
            "major": build_data["MajorVersion"],
            "minor": build_data["MinorVersion"],
            "patch": build_data["PatchVersion"],
            "changelist": build_data.get("Changelist"),
            "compatible_changelist": build_data.get("CompatibleChangelist"),
            "branch_name": build_data.get("BranchName"),
        },
        "mover": {
            "plugin_found": mover_descriptor is not None,
            "descriptor": str(mover_descriptor) if mover_descriptor is not None else None,
            "plugin_root": str(mover_root) if mover_root is not None else None,
            "readme_found": bool(mover_root and (mover_root / "README.md").is_file()),
            "source_found": bool(mover_root and (mover_root / "Source").is_dir()),
        },
    }


def collect_manifest(
    root: Path,
    verbose: bool,
    engine_root: Path | None = None,
) -> dict[str, Any]:
    project_path = find_single_project(root)
    project_data = load_json(project_path)
    association = project_data.get("EngineAssociation")
    if association is not None and not isinstance(association, str):
        raise ValueError(f"{project_path}: $.EngineAssociation 必须为字符串或 null")
    lgf_path = find_lgf_plugin(root)
    lgf_resolved = lgf_path.resolve() if lgf_path is not None else None
    lgf_data = load_json(lgf_path) if lgf_path is not None else None
    project_build_files, lgf_build_files = collect_build_files(root, lgf_path)

    lgf_modules = descriptor_modules(lgf_data, lgf_path) if lgf_data is not None else []
    lgf_source = lgf_path.parent / "Source" if lgf_path is not None else None
    lgf_headers = [path for path in lgf_source.glob("**/*.h") if path.is_file()] if lgf_source and lgf_source.is_dir() else []
    lgf_sources = [path for path in lgf_source.glob("**/*.cpp") if path.is_file()] if lgf_source and lgf_source.is_dir() else []
    source_inspectable = bool(lgf_build_files and (lgf_headers or lgf_sources))

    manifest: dict[str, Any] = {
        "workspace_root": str(root),
        "project": {
            "file": project_path.name,
            "engine_association": association,
            "engine_association_is_not_verified_version": True,
            "modules": descriptor_modules(project_data, project_path),
            "relevant_plugins": plugin_summary(project_data, project_path),
            "agents_file": (root / "AGENTS.md").is_file(),
        },
        "engine": inspect_engine(engine_root),
        "lgf": {
            "status": "found" if lgf_path is not None else "not_found_in_project",
            "search_scope": "project_plugins_only",
            "runtime_enabled_verified": False,
            "found": lgf_path is not None,
            "file": display_path(root, lgf_path) if lgf_path is not None else None,
            "resolved_file": str(lgf_resolved) if lgf_resolved is not None else None,
            "descriptor_outside_project": not lgf_resolved.is_relative_to(root.resolve()) if lgf_resolved is not None else None,
            "version_name": lgf_data.get("VersionName") if lgf_data is not None else None,
            "module_count": len(lgf_modules),
            "source_inspectable": source_inspectable,
            "build_file_count": len(lgf_build_files),
            "header_count": len(lgf_headers),
            "source_file_count": len(lgf_sources),
            "documents": {
                name: bool(lgf_path and (lgf_path.parent / name).is_file())
                for name in LGF_DOCUMENT_NAMES
            },
        },
        "build_files": {
            "project": display_paths(root, project_build_files),
            "lgf_count": len(lgf_build_files),
        },
        "has_git_metadata": (root / ".git").exists(),
        "limitations": [
            "未读取 .uasset 内部属性",
            "source_inspectable 仅表示发现 Build.cs 及源码文件；未验证模块完整性、编译或运行",
            "engine.verified 仅验证提供的 Build.version 版本字段；不证明引擎安装完整、与 EngineAssociation 匹配、可运行或当前 Editor 已连接",
            "文件清点允许符号链接指向文件；显示路径不证明实际内容位于工程根内",
            "LGF 仅搜索工程 Plugins；未搜索 Engine/Plugins 或额外插件目录，未找到不证明未安装",
            "relevant_plugins 仅记录 .uproject 显式声明；null 表示 Enabled 未声明，不代表运行时禁用或启用",
            "未识别或验证 GASP 样例来源与资产修订；需要项目清单和 Unreal 资产报告",
            "未修改或保存任何工程文件",
        ],
    }
    if engine_root is None:
        manifest["limitations"].append("未提供实际 Unreal Engine 根目录；EngineAssociation 未被当作语义版本")
    if verbose:
        manifest["lgf"]["modules"] = lgf_modules
        manifest["build_files"]["lgf"] = display_paths(root, lgf_build_files)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="只读检查 LGF/GASP/Mover 工程清单，并输出 JSON。"
    )
    parser.add_argument("project_root", type=Path, help="包含唯一 .uproject 的工程根目录")
    parser.add_argument(
        "--engine-root",
        type=Path,
        help="可选的实际 Unreal Engine 根目录；提供后读取 Engine/Build/Build.version",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="额外输出全部 LGF 模块和 Build.cs 路径",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.project_root.expanduser().resolve()
    if not root.is_dir():
        print(f"错误：工程根目录不存在：{root}", file=sys.stderr)
        return 2
    try:
        manifest = collect_manifest(root, args.verbose, args.engine_root)
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    try:
        # Complete encoding before touching stdout; ASCII escapes preserve JSON values.
        encoded = json.dumps(manifest, ensure_ascii=True, indent=2)
    except (ValueError, RecursionError, MemoryError) as exc:
        print(f"错误：JSON 编码失败：{root}: {type(exc).__name__}", file=sys.stderr)
        return 2
    try:
        print(encoded, flush=True)
    except (OSError, ValueError) as exc:
        print(f"错误：JSON 输出失败，输出可能不完整：{type(exc).__name__}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
