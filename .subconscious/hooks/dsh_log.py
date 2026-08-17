"""
dsh_log — DSH 环境变量通道的学情记录入口。

Windows PowerShell 5.1 的 legacy 原生参数传递会把命令行里的中文
按 GBK 处理，导致 python -c 内嵌中文乱码。环境变量通道无损，
因此本脚本从环境变量读取事件参数，供模型在会话中调用。

用法（cwd = 工作区根）：
    $env:EVENT_TEXT='用户学完太阳病篇第12条桂枝汤证'
    $env:EVENT_TAGS='伤寒论,太阳病,桂枝汤'
    $env:EVENT_TYPE='insight'
    python .subconscious/hooks/dsh_log.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hooks.session_logger import log  # noqa: E402

text = os.environ.get("EVENT_TEXT", "").strip()
if not text:
    print("[subconscious] EVENT_TEXT 为空，未记录")
    sys.exit(1)

tags_raw = os.environ.get("EVENT_TAGS", "").strip()
tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
event_type = os.environ.get("EVENT_TYPE", "note").strip() or "note"

log(text, tags=tags, event_type=event_type)
print(f"[subconscious] 已记录学情: {event_type} | tags={tags}")
