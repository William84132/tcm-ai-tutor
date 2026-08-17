"""
Session Logger — 会话日志记录器

意识层（我）在对话中主动记录关键事件到 session_log.jsonl。
SessionEnd hook 读取此文件，喂给潜意识管道处理。

每次记录格式（一行 JSON）：
  {"text": "事件描述", "tags": ["tag1", "tag2"], "type": "decision|problem|pattern|insight"}
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

SESSION_LOG = Path(__file__).resolve().parent.parent / "session_log.jsonl"


def log(text: str, tags: Optional[list[str]] = None, event_type: str = "note") -> None:
    """
    记录一条会话事件到 session_log.jsonl。

    由意识层（我）在每次对话中调用，用于捕获：
      - 关键决策（decision）
      - 问题/ Bug（problem）
      - 行为模式（pattern）
      - 知识/洞察（insight）

    Args:
        text: 事件描述（尽量简洁完整的一句话）
        tags: 标签列表，如 ["db", "debug", "perf"]
        event_type: 事件类型
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "text": text,
        "tags": tags or [],
    }
    try:
        with open(str(SESSION_LOG), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:
        # 静默失败——日志记录不应影响主流程
        pass


def clear() -> None:
    """清空会话日志（SessionEnd 处理完后调用）。"""
    try:
        if SESSION_LOG.exists():
            SESSION_LOG.unlink()
    except OSError:
        pass


def count() -> int:
    """统计当前日志条数。"""
    try:
        if not SESSION_LOG.exists():
            return 0
        text = SESSION_LOG.read_text(encoding="utf-8").strip()
        return len([l for l in text.split("\n") if l.strip()])
    except Exception:
        return 0
