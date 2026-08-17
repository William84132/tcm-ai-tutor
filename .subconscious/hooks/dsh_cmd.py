"""
dsh_cmd — 潜意识手动命令入口（DSH 环境变量通道）。

Windows PowerShell 5.1 下命令行中文会乱码，故关键词走环境变量。

用法（cwd = 工作区根）：
    python .subconscious/hooks/dsh_cmd.py status          # 查看记忆状态
    $env:EVENT_TEXT='少阴'; python .subconscious/hooks/dsh_cmd.py recall   # 召回相关记忆
    python .subconscious/hooks/dsh_cmd.py dream           # 触发一次梦境处理
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.storage import Storage  # noqa: E402
from core.dream import DreamEngine  # noqa: E402

cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
storage = Storage()

if cmd == "status":
    stats = storage.stats()
    print(f"[subconscious] 现状: {stats['active']} 活跃 / {stats['archived']} 归档, "
          f"关联 {stats['relations']}, 凝缩 {stats['condensations']}")
elif cmd == "recall":
    query = os.environ.get("EVENT_TEXT", "").strip()
    if not query:
        print("[subconscious] 请设置 $env:EVENT_TEXT 为召回关键词")
        sys.exit(1)
    results = storage.search(query)
    if not results:
        print(f"[subconscious] 未找到与「{query}」相关的记忆")
    else:
        print(f"🔍 与「{query}」相关的记忆 ({len(results)} 条):")
        for r in results[:10]:
            status = "📦" if r.archived else "📄"
            print(f"  {status} [{r.memory_type.value}] {r.memory_id} — {r.title} (重要性: {r.importance_total:.2f})")
elif cmd == "dream":
    report = DreamEngine(storage).process()
    print(f"[subconscious] 梦境: 跨会话链接 {report['cross_session_links']} 条, "
          f"新模式 {len(report['new_procedural'])} 个")
else:
    print(f"[subconscious] 未知命令: {cmd}（可用 status / recall / dream）")
