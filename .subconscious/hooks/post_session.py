"""
post_session — 会话结束钩子

v2 改动（2026-09-01）：
    1. 数据源从临时缓冲 .subconscious/session_log.jsonl 改为持久记忆
       <项目根>/.workbuddy/memory/sessions/session-memory.jsonl
    2. 只读取"上次处理后新增"的条目（靠 .session_memory_pointer 去重），
       避免每次会话重复编码全部历史
    3. 处理完只推进指针，**绝不删除记忆文件**（v1 的 unlink 会摧毁长期记忆）
    4. 先 migrate_legacy() 把旧缓冲并入持久记忆（幂等，重复跑安全）
"""

import sys, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from memory.storage import Storage
from memory.encoder import encode_simple
from core.subconscious import SubconsciousPipeline
from core.dream import DreamEngine
from hooks.session_logger import (
    migrate_legacy, unprocessed, mark_processed, memory_file,
)

# 先把旧缓冲并入持久记忆（幂等）
migrate_legacy()

storage = Storage()
pipeline = SubconsciousPipeline(storage)
dream = DreamEngine(storage)

# ── 1. 读取本次新增的会话记忆（仅未处理部分） ──
memories = []
for event in unprocessed("project"):
    text = event.get("text", "")
    if text:
        memories.append(encode_simple(
            context=text[:120],
            summary=text[:500],
            project=event.get("project", "subconscious"),
            tags=event.get("tags", []),
        ))

# ── 2. 执行完整管道 ──
if memories:
    result = pipeline.run(manual_memories=memories)
    print(f"[subconscious] 管道: 编码{result['stages']['1_encoding']['segments_created']}段 "
          f"| 联想{result['stages']['2_association']['relations_created']}条 "
          f"| 凝缩{result['stages']['3_condensation']['insights_created']}个 "
          f"| 固化提升{result['stages']['4_consolidation']['boosted']}条 "
          f"| whisper{result['stages']['5_pre_inject']['whisper_messages']}条")
else:
    print(f"[subconscious] 本次无新增会话记忆，跳过管道")

# ── 3. 遗忘扫描 ──
forget = pipeline.consolidator.forget_scan()
print(f"[subconscious] 遗忘扫描: 归档 {forget['archived']} 条, 新凝缩 {forget['condensed_this_round']} 条")

# ── 4. 梦境处理 ──
dream_report = dream.process()
print(f"[subconscious] 梦境: 跨会话链接 {dream_report['cross_session_links']} 条, 新模式 {len(dream_report['new_procedural'])} 个")

# ── 5. 推进处理指针（不清空记忆文件） ──
mark_processed("project")
print(f"[subconscious] 已处理并推进指针；记忆文件保留于 {memory_file('project')}")
