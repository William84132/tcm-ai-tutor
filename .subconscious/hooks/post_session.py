"""
post_session — 会话结束钩子

从 session_log.jsonl 读取本次会话的关键事件，运行完整潜意识管道。
同时在后台执行遗忘扫描 + 梦境处理。
"""
import sys, pathlib, json

root = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from memory.storage import Storage
from memory.encoder import encode_simple
from core.subconscious import SubconsciousPipeline
from core.dream import DreamEngine

storage = Storage()
pipeline = SubconsciousPipeline(storage)
dream = DreamEngine(storage)

# ── 1. 读取会话日志（逐事件编码：每行 = 一条独立记忆） ──
session_log = root / "session_log.jsonl"
memories = []

if session_log.exists():
    try:
        lines = session_log.read_text(encoding="utf-8").strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                text = event.get("text", "")
                if text:
                    memories.append(encode_simple(
                        context=text[:120],
                        summary=text[:500],
                        project="subconscious",
                        tags=event.get("tags", []),
                    ))
            except json.JSONDecodeError:
                continue
    except Exception as e:
        print(f"[subconscious] 读取 session_log 失败: {e}")

# ── 2. 执行完整管道（manual_memories 保留事件粒度与各自标签） ──
if memories:
    result = pipeline.run(manual_memories=memories)
    print(f"[subconscious] 管道: 编码{result['stages']['1_encoding']['segments_created']}段 "
          f"| 联想{result['stages']['2_association']['relations_created']}条 "
          f"| 凝缩{result['stages']['3_condensation']['insights_created']}个 "
          f"| 固化提升{result['stages']['4_consolidation']['boosted']}条 "
          f"| whisper{result['stages']['5_pre_inject']['whisper_messages']}条")
else:
    print(f"[subconscious] 无会话日志，跳过管道")

# ── 3. 遗忘扫描 ──
forget = pipeline.consolidator.forget_scan()
print(f"[subconscious] 遗忘扫描: 归档 {forget['archived']} 条, 新凝缩 {forget['condensed_this_round']} 条")

# ── 4. 梦境处理 ──
dream_report = dream.process()
print(f"[subconscious] 梦境: 跨会话链接 {dream_report['cross_session_links']} 条, 新模式 {len(dream_report['new_procedural'])} 个")

# ── 5. 清理会话日志 ──
if session_log.exists():
    session_log.unlink()

# ── 6. 统计 ──
stats = storage.stats()
print(f"[subconscious] 现状: {stats['active']} 活跃 / {stats['archived']} 归档, 关联 {stats['relations']}, 凝缩 {stats['condensations']}")
