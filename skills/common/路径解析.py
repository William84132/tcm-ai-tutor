# -*- coding: utf-8 -*-
"""
路径权威 —— 全系统唯一路径解析入口（v1.0）

背景（2026-09-01 修复）：
    此前各 SKILL.md 用裸相对路径 `../01-经典临床（正课）/` 声明笔记位置，
    而"运行副本"与"发布版"两套目录树的层级结构不同（运行副本 skills 在
    vault 内，发布版 skills 在仓库根），同一句相对路径解析出两个不存在
    的目录，导致读写目录错开、备份读到空数据。

铁律：
    1. 任何技能、任何脚本、任何 AI 会话都不得再写裸相对路径定位 vault /
       笔记 / 记忆；一律调用本模块。
    2. 解析失败必须抛 PathResolveError 让上层停下来问用户，
       严禁 fallback 到"仓库根目录"或"当前工作目录"瞎猜。
    3. 记忆一律禁止写入 .env / config.json / users.db 等配置与密钥文件。

用法：
    from 路径解析 import note_dir, memory_file, VAULT_ROOT, PROJECT_ROOT

    PROJECT_ROOT              # 含 .workbuddy/.git/CLAUDE.md 的目录（向上查找得到）
    VAULT_ROOT                # 含 .obsidian 的目录（发布版无 .obsidian 时回退 00-原著全文+08-学习工具）
    note_dir("01-经典临床（正课）", ensure=True)
    memory_file("project")    # <项目根>/.workbuddy/memory/sessions/session-memory.jsonl
    memory_file("global")     # ~/.workbuddy/memory/sessions/session-memory.jsonl
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional

__version__ = "1.0"

# ---------------------------------------------------------------- 标记定义

# 项目根标记（命中任一即认为找到项目根）
PROJECT_MARKERS: tuple[str, ...] = (".workbuddy", ".git", "CLAUDE.md")

# vault 首选标记：Obsidian 库
VAULT_MARKER_PRIMARY = ".obsidian"

# vault 回退标记：发布版不带 .obsidian，用课程目录组合判定
VAULT_MARKERS_FALLBACK: tuple[str, ...] = ("00-原著全文", "08-学习工具")

# 课程笔记目录（用于校验解析结果是否可信）
COURSE_DIR_HINTS: tuple[str, ...] = (
    "01-经典临床（正课）", "02-经典临床（复习）",
    "03-黄帝内经（正课）", "04-黄帝内经（复习）",
    "05-经典基础", "06-诊疗基础", "07-温病历史课（旧）",
)

# 会话记忆文件名（全局统一，一行一个 JSON）
MEMORY_FILENAME = "session-memory.jsonl"

# 会话记忆目录名（位于 memory 之下）
MEMORY_SUBDIR = "sessions"

# 禁止写入记忆的敏感文件名（配置 / 密钥 / 账号库）
FORBIDDEN_TARGETS: tuple[str, ...] = (".env", "config.json", "users.db")


class PathResolveError(RuntimeError):
    """路径解析失败。上层必须停下来询问用户，不得猜测。"""


class SensitiveTargetError(RuntimeError):
    """试图把记忆写入配置 / 密钥文件。"""


# ---------------------------------------------------------------- 基础解析

def _here() -> Path:
    return Path(__file__).resolve().parent


def find_project_root(start: Optional[Path | str] = None) -> Path:
    """向上查找项目根：第一个含 .workbuddy / .git / CLAUDE.md 的目录。"""
    cur = Path(start).resolve() if start else _here()
    if cur.is_file():
        cur = cur.parent
    for cand in (cur, *cur.parents):
        if any((cand / m).exists() for m in PROJECT_MARKERS):
            return cand
    raise PathResolveError(
        f"未找到项目根（自 {cur} 向上均未发现 {'/'.join(PROJECT_MARKERS)}）。"
        "禁止猜测路径，请向用户确认项目根目录后再继续。"
    )


def _is_vault(d: Path) -> bool:
    """主标记：含 .obsidian。"""
    return (d / VAULT_MARKER_PRIMARY).is_dir()


def _is_vault_fallback(d: Path) -> bool:
    """回退标记：含 00-原著全文 与 08-学习工具（发布版无 .obsidian）。"""
    return all((d / m).is_dir() for m in VAULT_MARKERS_FALLBACK)


def find_vault_root(project_root: Optional[Path | str] = None) -> Path:
    """
    定位 vault 根（笔记库）。

    解析顺序：
      1. 项目根自身含 .obsidian
      2. 项目根的直接子目录含 .obsidian（运行副本：<项目根>/叶天士）
      3. 项目根自身或直接子目录同时含 00-原著全文 + 08-学习工具（发布版）
    全部失败则抛错。
    """
    root = Path(project_root).resolve() if project_root else find_project_root()

    if _is_vault(root):
        return root
    for child in sorted(p for p in root.iterdir() if p.is_dir()):
        if _is_vault(child):
            return child
    if _is_vault_fallback(root):
        return root
    for child in sorted(p for p in root.iterdir() if p.is_dir()):
        if _is_vault_fallback(child):
            return child

    raise PathResolveError(
        f"未找到 vault 根（在 {root} 及其直接子目录中，既无 {VAULT_MARKER_PRIMARY}/，"
        f"也无 {'+'.join(VAULT_MARKERS_FALLBACK)}）。禁止在仓库根层新建笔记，请向用户确认。"
    )


def find_skills_root(project_root: Optional[Path | str] = None) -> Path:
    """定位 skills 目录：优先取本文件所在 skills/common 的上一级，失败再全库搜。"""
    here = _here()
    if here.name == "common" and (here.parent / "common" / "核心机制.md").exists():
        return here.parent
    root = Path(project_root).resolve() if project_root else find_project_root()
    for cand in root.rglob("skills"):
        if (cand / "common" / "核心机制.md").exists():
            return cand
    raise PathResolveError(f"未找到 skills 目录（自 {root} 未发现 skills/common/核心机制.md）。")


# ---------------------------------------------------------------- 记忆路径

def _assert_not_sensitive(path: Path) -> Path:
    name = path.name.lower()
    if name in FORBIDDEN_TARGETS or name.startswith(".env"):
        raise SensitiveTargetError(
            f"禁止把记忆写入 {path.name}（配置/密钥/账号文件，且被 .gitignore 排除，必然丢失）。"
            "请改用 memory_file()。"
        )
    return path


def memory_dir(scope: str = "project", project_root: Optional[Path | str] = None) -> Path:
    """
    会话记忆目录。

    scope = "project" → <项目根>/.workbuddy/memory/sessions/
    scope = "global"  → ~/.workbuddy/memory/sessions/

    判定规则：默认 project；只有结论"跨项目复用"时才用 global。
    """
    scope = (scope or "project").lower()
    if scope == "global":
        base = Path.home() / ".workbuddy" / "memory"
    elif scope == "project":
        base = find_project_root(project_root) / ".workbuddy" / "memory"
    else:
        raise PathResolveError(f"未知 scope: {scope!r}（只能是 'project' 或 'global'）")
    return base / MEMORY_SUBDIR


def memory_file(scope: str = "project", project_root: Optional[Path | str] = None) -> Path:
    """会话记忆文件（自动建目录）。"""
    d = memory_dir(scope, project_root)
    d.mkdir(parents=True, exist_ok=True)
    return _assert_not_sensitive(d / MEMORY_FILENAME)


def skill_memory_file(skill_name: str, project_root: Optional[Path | str] = None) -> Path:
    """
    技能归属副本：skills/<技能名>/memory/session-memory.jsonl

    只存放"本技能产生的会话"，便于按技能维度筛选与整体搬迁。
    """
    root = find_skills_root(project_root) / skill_name / "memory"
    root.mkdir(parents=True, exist_ok=True)
    return _assert_not_sensitive(root / MEMORY_FILENAME)


# ---------------------------------------------------------------- 笔记路径

def note_dir(course: str, ensure: bool = False,
             project_root: Optional[Path | str] = None) -> Path:
    """
    课程笔记目录 = <VAULT_ROOT>/<course>

    course 示例："01-经典临床（正课）"、"05-经典基础"
    ensure=True 时自动建目录（新建课程时用；平时建议 False 以便暴露路径错误）。
    """
    p = find_vault_root(project_root) / course
    if ensure:
        p.mkdir(parents=True, exist_ok=True)
    return p


def note_file(course: str, filename: str,
              project_root: Optional[Path | str] = None) -> Path:
    """课程笔记文件路径（自动建目录）。"""
    d = note_dir(course, ensure=True, project_root=project_root)
    return d / filename


# ---------------------------------------------------------------- 自检

def describe(project_root: Optional[Path | str] = None) -> str:
    """打印全部解析结果，供路径自检 / 备份前校验使用。"""
    root = find_project_root(project_root)
    lines = [
        f"项目根 PROJECT_ROOT : {root}",
        f"笔记库 VAULT_ROOT   : {find_vault_root(root)}",
        f"技能库 SKILLS_ROOT  : {find_skills_root(root)}",
        f"项目记忆            : {memory_file('project', root)}",
        f"全局记忆            : {memory_file('global')}",
    ]
    vault = find_vault_root(root)
    found = [d for d in COURSE_DIR_HINTS if (vault / d).is_dir()]
    lines.append(f"已存在课程目录      : {found or '（无，首次使用属正常）'}")
    return "\n".join(lines)


# 模块级常量（导入即用；延迟到调用时解析，避免导入期抛错）
def __getattr__(name: str):
    if name == "PROJECT_ROOT":
        return find_project_root()
    if name == "VAULT_ROOT":
        return find_vault_root()
    if name == "SKILLS_ROOT":
        return find_skills_root()
    raise AttributeError(name)


if __name__ == "__main__":
    print(describe())
