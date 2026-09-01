# -*- coding: utf-8 -*-
"""
Session Logger v2 — 会话记忆记录器

v2 改动（2026-09-01）：
    1. 存储位置：session_log.jsonl（临时缓冲，post_session 跑完会删）
                → session-memory.jsonl（持久记忆，永不自动清空）
    2. 双路径：scope="project" 写 <项目根>/.workbuddy/memory/sessions/
              scope="global"  写 ~/.workbuddy/memory/sessions/
    3. 归属字段：每条带 session_id / scope / project / skill，
       只有 skill 字段匹配的会话才算"本技能产生的会话"。
    4. 二套迁移检查：旧 .subconscious/session_log.jsonl 存在时自动按
       (timestamp, text) 去重复制到新位置，源文件只归档不删除。
    5. 禁止写入 .env / config.json / users.db 等配置密钥文件。

记录格式（一行一个 JSON）：
    {"ts": "...", "session_id": "...", "scope": "project", "project": "叶天士",
     "skill": "经典临床", "type": "insight", "text": "...", "tags": [...]}
"""

from __future__ import annotations

import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------- 路径解析

_HERE = Path(__file__).resolve().parent          # <项目根>/.subconscious/hooks
_ROOT = _HERE.parent                              # <项目根>/.subconscious

_PROJECT_MARKERS = (".workbuddy", ".git", "CLAUDE.md")
_FORBIDDEN_TARGETS = (".env", "config.json", "users.db")

MEMORY_FILENAME = "session-memory.jsonl"
MEMORY_SUBDIR = "sessions"

LEGACY_SESSION_LOG = _ROOT / "session_log.jsonl"
POINTER_FILE = _ROOT / ".session_memory_pointer"

# 会话 ID：同一会话内多进程调用共享（由宿主注入环境变量）
SESSION_ID = os.environ.get("DSH_SESSION_ID") or os.environ.get("SESSION_ID") or \
    "{0:%Y%m%d}-{1}-{2}".format(datetime.now(), os.getppid(), uuid.uuid4().hex[:6])


class PathResolveError(RuntimeError):
    pass


class SensitiveTargetError(RuntimeError):
    pass


def find_project_root(start: Optional[Path] = None) -> Path:
    """向上查找项目根：第一个含 .workbuddy / .git / CLAUDE.md 的目录。"""
    cur = Path(start) if start else _HERE
    for cand in (cur, *cur.parents):
        if any((cand / m).exists() for m in _PROJECT_MARKERS):
            return cand
    raise PathResolveError(
        f"未找到项目根（自 {cur} 向上均未发现 {'/'.join(_PROJECT_MARKERS)}）。"
        "禁止猜测路径，请向用户确认后再继续。"
    )


def _assert_not_sensitive(p: Path) -> Path:
    name = p.name.lower()
    if name in _FORBIDDEN_TARGETS or name.startswith(".env"):
        raise SensitiveTargetError(
            f"禁止把记忆写入 {p.name}（配置/密钥/账号文件，且被 .gitignore 排除，必然丢失）。"
        )
    return p


def memory_dir(scope: str = "project") -> Path:
    """scope=project → <项目根>/.workbuddy/memory/sessions/ ；scope=global → ~/.workbuddy/memory/sessions/"""
    scope = (scope or "project").lower()
    if scope == "global":
        base = Path.home() / ".workbuddy" / "memory"
    elif scope == "project":
        base = find_project_root() / ".workbuddy" / "memory"
    else:
        raise PathResolveError(f"未知 scope: {scope!r}（只能是 'project' 或 'global'）")
    return base / MEMORY_SUBDIR


def memory_file(scope: str = "project") -> Path:
    """持久会话记忆文件（自动建目录）。"""
    d = memory_dir(scope)
    d.mkdir(parents=True, exist_ok=True)
    return _assert_not_sensitive(d / MEMORY_FILENAME)


def skill_memory_file(skill_name: str) -> Path:
    """技能归属副本：skills/<技能名>/memory/session-memory.jsonl"""
    root = find_project_root()
    for cand in root.rglob("skills"):
        if (cand / "common" / "核心机制.md").exists():
            d = cand / skill_name / "memory"
            d.mkdir(parents=True, exist_ok=True)
            return _assert_not_sensitive(d / MEMORY_FILENAME)
    raise PathResolveError(f"未找到 skills 目录（自 {root}）。")


def _resolve(scope: str = "project", skill: Optional[str] = None) -> Path:
    """skill 非空时双写：主副本 + 技能归属副本（主副本为唯一真源）。"""
    return memory_file(scope)


# 兼容旧名：模块常量（惰性求值由函数承担，保留给外部 import）
SESSION_LOG = memory_file("project")


# ---------------------------------------------------------------- 写入

def log(text: str,
        tags: Optional[list] = None,
        event_type: str = "note",
        skill: Optional[str] = None,
        scope: str = "project") -> dict:
    """
    记录一条会话事件到 session-memory.jsonl。

    Args:
        text:       事件描述（简洁完整的一句话）
        tags:       标签列表
        event_type: note|decision|problem|pattern|insight
        skill:      产生该会话的技能名（如 "经典临床"）。
                    ——关键字段：只有本技能产生的会话才值得保存与筛选。
        scope:      "project"（默认）| "global"（跨项目复用的结论）
    """
    entry = {
        "ts": datetime.now().isoformat(),
        "session_id": SESSION_ID,
        "scope": scope,
        "project": find_project_root().name,
        "skill": skill,
        "type": event_type,
        "text": text,
        "tags": tags or [],
    }

    primary = memory_file(scope)
    line = json.dumps(entry, ensure_ascii=False)
    try:
        with open(str(primary), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass  # 记录失败不应影响主流程

    # 技能归属副本（与主副本内容一致，便于按技能维度整体搬迁）
    if skill:
        try:
            with open(str(skill_memory_file(skill)), "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except (OSError, PathResolveError):
            pass

    return entry


# ---------------------------------------------------------------- 读取

def _read_lines(path: Path) -> list:
    if not path.exists():
        return []
    try:
        return [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return []


def count(scope: str = "project") -> int:
    """统计持久记忆条数。"""
    return len(_read_lines(memory_file(scope)))


def read_all(scope: str = "project") -> list:
    """读取全部记忆条目（解析失败的行自动跳过）。"""
    out = []
    for line in _read_lines(memory_file(scope)):
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def by_skill(skill: str, scope: str = "project") -> list:
    """筛选某个技能产生的会话（用户核心诉求：只保留本 skill 的会话）。"""
    return [e for e in read_all(scope) if e.get("skill") == skill]


def _pointer_file(scope: str) -> Path:
    """指针按 scope 分开存放，避免项目级与全局级互相干扰。"""
    if scope == "global":
        return memory_dir("global") / ".pointer"
    return POINTER_FILE


def _pointer(scope: str = "project") -> int:
    pf = _pointer_file(scope)
    if pf.exists():
        try:
            return int(pf.read_text(encoding="utf-8").strip() or 0)
        except Exception:
            return 0
    # 首次运行：把"此刻已存在的条目"视为已处理，
    # 避免历史数据（含刚迁移的旧缓冲）被重复灌进潜意识管道
    n = len(_read_lines(memory_file(scope)))
    _set_pointer(n, scope)
    return n


def _set_pointer(n: int, scope: str = "project") -> None:
    try:
        _pointer_file(scope).write_text(str(n), encoding="utf-8")
    except OSError:
        pass


def unprocessed(scope: str = "project") -> list:
    """供 post_session 使用：读取上次处理之后新增的条目。"""
    lines = _read_lines(memory_file(scope))
    return [json.loads(l) for l in lines[_pointer(scope):] if _safe_json(l)]


def _safe_json(line: str):
    try:
        json.loads(line)
        return True
    except json.JSONDecodeError:
        return False


def mark_processed(scope: str = "project") -> None:
    """post_session 处理完后推进指针（不清空记忆文件）。"""
    _set_pointer(len(_read_lines(memory_file(scope))), scope)


# ---------------------------------------------------------------- 迁移与归档

def migrate_legacy(scope: str = "project") -> int:
    """
    二套迁移检查：把旧 .subconscious/session_log.jsonl 的内容去重复制到
    session-memory.jsonl。源文件只归档、不删除。返回迁移条数。
    """
    if not LEGACY_SESSION_LOG.exists():
        return 0

    target = memory_file(scope)
    existing = set()
    for e in read_all(scope):
        existing.add((e.get("ts") or e.get("timestamp"), e.get("text")))

    moved = 0
    for line in _read_lines(LEGACY_SESSION_LOG):
        try:
            old = json.loads(line)
        except json.JSONDecodeError:
            continue
        key = (old.get("timestamp"), old.get("text"))
        if key in existing or not old.get("text"):
            continue
        entry = {
            "ts": old.get("timestamp") or datetime.now().isoformat(),
            "session_id": old.get("session_id", "legacy"),
            "scope": scope,
            "project": find_project_root().name,
            "skill": old.get("skill"),
            "type": old.get("type", "note"),
            "text": old.get("text"),
            "tags": old.get("tags", []),
            "migrated_from": ".subconscious/session_log.jsonl",
        }
        try:
            with open(str(target), "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            moved += 1
        except OSError:
            break

    if moved:
        _archive_legacy()
    return moved


def _archive_legacy() -> Optional[Path]:
    """旧缓冲迁移完成后归档（绝不删除），返回归档路径。"""
    if not LEGACY_SESSION_LOG.exists():
        return None
    stamp = "{0:%Y%m%d_%H%M%S}".format(datetime.now())
    dest = _ROOT / f"已迁移_session_log_{stamp}.jsonl"
    try:
        shutil.copy2(str(LEGACY_SESSION_LOG), str(dest))
        LEGACY_SESSION_LOG.unlink()
        return dest
    except OSError:
        return None


def archive(scope: str = "project") -> Optional[Path]:
    """手动轮转：把当前记忆另存为 session-memory.归档_时间戳.jsonl，原文件清空。"""
    src = memory_file(scope)
    if not src.exists():
        return None
    stamp = "{0:%Y%m%d_%H%M%S}".format(datetime.now())
    dest = src.parent / f"session-memory.归档_{stamp}.jsonl"
    shutil.copy2(str(src), str(dest))
    src.write_text("", encoding="utf-8")
    _set_pointer(0)
    return dest


def clear() -> None:
    """
    已废弃：v1 的 clear() 会删除会话日志，v2 中持久记忆禁止静默清空。
    需要轮转请显式调用 archive()。
    """
    raise RuntimeError(
        "clear() 已废弃：session-memory.jsonl 是持久记忆，禁止静默清空。"
        "如需轮转请调用 archive()，如需清理临时缓冲请处理 .subconscious/session_log.jsonl。"
    )


if __name__ == "__main__":
    print("项目根        :", find_project_root())
    print("项目记忆文件  :", memory_file("project"))
    print("全局记忆文件  :", memory_file("global"))
    print("旧缓冲        :", LEGACY_SESSION_LOG, "(存在)" if LEGACY_SESSION_LOG.exists() else "(不存在)")
    print("当前记忆条数  :", count("project"))
    n = migrate_legacy()
    print(f"迁移旧缓冲    : {n} 条")
    print("迁移后条数    :", count("project"))
