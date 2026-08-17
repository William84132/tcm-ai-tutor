"""
Dream — 梦境处理引擎

职责：
  - 在空闲/定时运行时，对记忆做"梦境式"重放
  - 交叉关联不同类型的记忆（情景↔语义↔程序）
  - 尝试建立新的跨会话链接
  - 生成"梦境型"松散联想

梦境不是随机的——它是潜意识在离线状态下对记忆的整理和再索引。
"""

from __future__ import annotations

from datetime import datetime
from random import sample
from typing import Any, Optional

from models.schemas import (
    EpisodicMemory, SemanticMemory, ProceduralMemory,
    MemoryRelation, RelationType, CondensedInsight,
    MemoryIndexEntry, MemoryType,
)
from memory.storage import Storage
from memory.associator import Associator
from memory.consolidator import Consolidator


class DreamEngine:
    """梦境处理引擎。"""

    def __init__(self, storage: Storage):
        self.storage = storage
        self.associator = Associator(storage)
        self.consolidator = Consolidator(storage)

    # ─────────────────────────────
    # 主入口
    # ─────────────────────────────

    def process(self) -> dict[str, Any]:
        """
        执行一次完整梦境处理。

        梦境流程：
          1. 交叉关联：情景 ↔ 语义 ↔ 程序 记忆之间的弱关联
          2. 跨会话链接：尝试链接不同会话的同类事件
          3. 模式提炼：从情景记忆中提炼程序记忆
          4. 松散联想：生成一个"梦境"whisper 候选
        """
        report: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "cross_relations": 0,
            "cross_session_links": 0,
            "new_procedural": [],
            "dream_whisper": "",
        }

        active = self.storage.list_active()
        if len(active) < 2:
            return report

        # 1) 交叉关联不同类型
        cross = self._cross_associate(active)
        report["cross_relations"] = len(cross)

        # 2) 跨会话链接
        links = self._cross_session_link(active)
        report["cross_session_links"] = len(links)

        # 3) 模式提炼
        procs = self.consolidator.extract_patterns()
        report["new_procedural"] = [p.memory_id for p in procs]

        # 4) 生成梦境 whisper 候选
        dream_msg = self._generate_dream_whisper(active)
        report["dream_whisper"] = dream_msg

        return report

    # ─────────────────────────────
    # 交叉关联
    # ─────────────────────────────

    def _cross_associate(self, entries: list[MemoryIndexEntry]) -> list[MemoryRelation]:
        """在不同类型的记忆之间建立弱关联。"""
        relations: list[MemoryRelation] = []

        episodic_ids = [e.memory_id for e in entries if e.memory_type == MemoryType.EPISODIC]
        semantic_ids = [e.memory_id for e in entries if e.memory_type == MemoryType.SEMANTIC]
        procedural_ids = [e.memory_id for e in entries if e.memory_type == MemoryType.PROCEDURAL]

        # 情景 ↔ 语义：标签匹配
        for eid in episodic_ids[:20]:
            ep_entry = next((e for e in entries if e.memory_id == eid), None)
            if not ep_entry:
                continue
            for sid in semantic_ids[:20]:
                sem_entry = next((e for e in entries if e.memory_id == sid), None)
                if not sem_entry:
                    continue
                # 检查标签重叠
                ep_tags = set(t.lower() for t in ep_entry.tags)
                sem_tags = set(t.lower() for t in sem_entry.tags)
                if ep_tags & sem_tags:
                    rel = MemoryRelation(
                        source_id=eid,
                        target_id=sid,
                        relation_type=RelationType.SYMBOLIC,
                        strength=0.3,
                        description="梦境交叉关联（标签重叠）",
                    )
                    self.storage.save_relation(rel)
                    relations.append(rel)

        return relations

    # ─────────────────────────────
    # 跨会话链接
    # ─────────────────────────────

    def _cross_session_link(self, entries: list[MemoryIndexEntry]) -> list[MemoryRelation]:
        """
        尝试在不同会话之间建立链接。

        策略：找同项目 + 时间相近但不直接关联的记忆。
        """
        relations: list[MemoryRelation] = []

        episodic_entries = [e for e in entries if e.memory_type == MemoryType.EPISODIC]
        if len(episodic_entries) < 3:
            return relations

        # 每组取两条，按标签匹配
        for i in range(len(episodic_entries)):
            for j in range(i + 1, len(episodic_entries)):
                ei = episodic_entries[i]
                ej = episodic_entries[j]

                # 如果已经有关联则跳过
                existing = self.storage.get_relations(ei.memory_id)
                if any(r.target_id == ej.memory_id or r.source_id == ej.memory_id for r in existing):
                    continue

                # 按标签匹配
                tags_i = set(t.lower() for t in ei.tags)
                tags_j = set(t.lower() for t in ej.tags)
                common = tags_i & tags_j
                if common:
                    rel = MemoryRelation(
                        source_id=ei.memory_id,
                        target_id=ej.memory_id,
                        relation_type=RelationType.TEMPORAL,
                        strength=0.4,
                        description=f"梦境跨会话链接（共同标签: {', '.join(common)}）",
                    )
                    self.storage.save_relation(rel)
                    relations.append(rel)

        return relations

    # ─────────────────────────────
    # 梦境 whisper 生成
    # ─────────────────────────────

    def _generate_dream_whisper(self, entries: list[MemoryIndexEntry]) -> str:
        """
        从记忆中生成一条"梦境"式的松散联想。不为精确，而为创意。

        方法：
          - 随机取两条不同类型的记忆
          - 尝试找出它们的潜在关联（即使很弱）
          - 格式化为"梦境"whisper
        """
        if len(entries) < 2:
            return ""

        episodic = [e for e in entries if e.memory_type == MemoryType.EPISODIC]
        semantic = [e for e in entries if e.memory_type == MemoryType.SEMANTIC]
        procedural = [e for e in entries if e.memory_type == MemoryType.PROCEDURAL]

        # 取两种不同类型的记忆
        candidates = []
        if episodic and semantic:
            candidates.append((sample(episodic, 1)[0], sample(semantic, 1)[0]))
        if episodic and procedural:
            candidates.append((sample(episodic, 1)[0], sample(procedural, 1)[0]))

        if not candidates:
            return ""

        a, b = sample(candidates, 1)[0]
        return (
            f"💭 [梦境联想]\n"
            f"「{a.title}」←→「{b.title}」\n"
            f"它们的共同标签: {set(a.tags) & set(b.tags)}"
        )
