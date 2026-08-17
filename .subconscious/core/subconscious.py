"""
Subconscious Pipeline — 潜意识处理管道

职责：串联所有 5 个处理阶段，是潜意识层的核心入口。

管道流程：
  Stage 1: 编码 (Encoder)       — transcript → 结构化记忆片段
  Stage 2: 联想 (Associator)    — 新记忆 ↔ 历史记忆关联
  Stage 3: 凝缩 (Consolidator)  — 同类聚类 → 抽象 insight
  Stage 4: 固化 (Consolidator)  — 写入 + 权重调整 + 衰减 + 归档
  Stage 5: 预注入 (Injector)    — 生成 whisper 包供下次会话

使用方式：
    from .subconscious.memory.storage import Storage
    from .subconscious.memory.encoder import encode_session
    storage = Storage()
    pipeline = SubconsciousPipeline(storage)
    result = pipeline.run(transcript=session_text, project="my-project")
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from models.schemas import (
    EpisodicMemory, SemanticMemory, ProceduralMemory,
    MemoryRelation, WhisperMessage, WhisperPackage,
    CondensedInsight, MemoryIndexEntry, MemoryType,
    RelationType, ImportanceScore,
)
from models.importance import (
    calc_base_initial, calc_frequency_bonus,
)
from memory.storage import Storage
from memory.encoder import encode_session, encode_simple
from memory.associator import Associator
from memory.consolidator import Consolidator


class SubconsciousPipeline:
    """潜意识处理管道主控器。"""

    def __init__(self, storage: Storage):
        self.storage = storage
        self.associator = Associator(storage)
        self.consolidator = Consolidator(storage)

    # ─────────────────────────────
    # 主入口：运行完整管道
    # ─────────────────────────────

    def run(
        self,
        transcript: str = "",
        project: str = "",
        tags: Optional[list[str]] = None,
        manual_memories: Optional[list[EpisodicMemory]] = None,
    ) -> dict[str, Any]:
        """
        运行潜意识处理管道（全部 5 个阶段）。

        Args:
            transcript: 会话文本（或关键事件摘要）
            project: 当前项目名
            tags: 用户提供的标签
            manual_memories: 手动创建的记忆（不走 encoder 编码）

        Returns:
            各阶段执行报告
        """
        report: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "stages": {},
            "new_memory_ids": [],
        }

        # ── Stage 1: 编码 ──
        new_memories: list[EpisodicMemory] = []
        if transcript:
            new_memories = encode_session(transcript, project=project, user_tags=tags)
        if manual_memories:
            new_memories.extend(manual_memories)

        report["stages"]["1_encoding"] = {
            "input_length": len(transcript),
            "segments_created": len(new_memories),
        }

        if not new_memories:
            report["stages"]["2_association"] = {"skipped": True}
            report["stages"]["3_condensation"] = {"skipped": True}
            report["stages"]["4_consolidation"] = {"skipped": True}
            report["stages"]["5_pre_inject"] = {"skipped": True}
            return report

        # 保存新记忆并收集 ID
        new_ids: list[str] = []
        for mem in new_memories:
            mid = self.storage.save_episodic(mem)
            new_ids.append(mid)
        report["new_memory_ids"] = new_ids

        # ── Stage 2: 联想 ──
        relation_count = 0
        for i, mem in enumerate(new_memories):
            relations = self.associator.associate(
                source_id=new_ids[i],
                source_text=mem.summary,
                source_tags=mem.tags,
                source_project=mem.project,
            )
            relation_count += len(relations)

        report["stages"]["2_association"] = {
            "relations_created": relation_count,
        }

        # ── Stage 3: 凝缩 ──
        insights = self.consolidator.condense(min_cluster=3)
        report["stages"]["3_condensation"] = {
            "insights_created": len(insights),
            "total_clusters": sum(i.cluster_size for i in insights),
        }

        # ── Stage 4: 固化 ──
        consolidation_result = self.consolidator.consolidate(new_ids)
        report["stages"]["4_consolidation"] = consolidation_result

        # ── Stage 5: 预注入 ──
        whisper_pkg = self._generate_whisper_package(new_ids)
        self.storage.save_whisper_package(whisper_pkg)
        report["stages"]["5_pre_inject"] = {
            "whisper_messages": len(whisper_pkg.messages),
        }

        return report

    # ─────────────────────────────
    # 单阶段运行（用于外部调用/手动触发）
    # ─────────────────────────────

    def run_encoding(
        self,
        transcript: str,
        project: str = "",
        tags: Optional[list[str]] = None,
    ) -> list[EpisodicMemory]:
        """只跑 Stage 1：编码。"""
        return encode_session(transcript, project=project, user_tags=tags)

    def run_association(self, memory_id: str, text: str, tags: Optional[list[str]] = None, project: str = "") -> list[MemoryRelation]:
        """只跑 Stage 2：联想。"""
        return self.associator.associate(
            source_id=memory_id,
            source_text=text,
            source_tags=tags,
            source_project=project,
        )

    def run_condensation(self, min_cluster: int = 3) -> list[CondensedInsight]:
        """只跑 Stage 3：凝缩。"""
        return self.consolidator.condense(min_cluster=min_cluster)

    def run_consolidation(self, new_memory_ids: list[str]) -> dict:
        """只跑 Stage 4：固化。"""
        return self.consolidator.consolidate(new_memory_ids)

    def run_pre_inject(self, new_memory_ids: list[str]) -> WhisperPackage:
        """只跑 Stage 5：预注入。"""
        pkg = self._generate_whisper_package(new_memory_ids)
        self.storage.save_whisper_package(pkg)
        return pkg

    # ─────────────────────────────
    # Stage 5: 预注入生成
    # ─────────────────────────────

    def _generate_whisper_package(self, new_memory_ids: list[str]) -> WhisperPackage:
        """
        生成预注入包——选择最高相关度的记忆片段打包为 whisper。

        策略：
          1. 优先选择刚固化的凝缩 insight
          2. 其次选择重要性最高的活跃记忆
          3. 最后选择本次新创建的高分记忆
        """
        pkg = WhisperPackage()

        # 1) 凝缩 insight
        for ci in reversed(self.storage.index.condensations[-5:]):  # 最近 5 条
            if len(pkg.messages) >= pkg.max_messages:
                break
            msg = WhisperMessage(
                source_memory_type="condensed_insight",
                source_memory_id=ci.insight_id,
                relation_description=f"聚类 {ci.cluster_size} 条记忆",
                suggestion=ci.implication,
            )
            pkg.add(msg)

        # 2) 高重要性活跃记忆
        active = self.storage.list_active()
        top_active = sorted(active, key=lambda e: e.importance_total, reverse=True)[:5]
        for entry in top_active:
            if len(pkg.messages) >= pkg.max_messages:
                break
            if entry.memory_id in new_memory_ids:
                continue
            msg = WhisperMessage(
                source_memory_type=entry.memory_type.value,
                source_memory_id=entry.memory_id,
                relation_description=f"高重要性记忆 (score={entry.importance_total:.2f})",
                suggestion=entry.title[:150],
            )
            pkg.add(msg)

        # 3) 新创建的高分记忆
        for mid in new_memory_ids:
            if len(pkg.messages) >= pkg.max_messages:
                break
            entry = self._find_entry(mid)
            if entry and entry.importance_total >= 0.7:
                msg = WhisperMessage(
                    source_memory_type="new",
                    source_memory_id=mid,
                    relation_description="本轮新创建的高分记忆",
                    suggestion=entry.title[:150],
                )
                pkg.add(msg)

        return pkg

    # ─────────────────────────────
    # 模式提取（由固化阶段触发）
    # ─────────────────────────────

    def extract_procedural_memories(self) -> list[ProceduralMemory]:
        """从活跃记忆中提取程序记忆（行为模式）。"""
        return self.consolidator.extract_patterns()

    # ─────────────────────────────
    # 梦境触发
    # ─────────────────────────────

    def dream_process(self) -> dict[str, Any]:
        """
        梦境处理——在空闲/定时时运行。
        行为：
          1. 强制凝缩（即使聚类 < 3 也尝试）
          2. 交叉关联不同类型的记忆
          3. 提取新的程序记忆
          4. 执行遗忘扫描
        """
        dream_report: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "condensations": [],
            "new_procedural": [],
            "forget_scan": {},
        }

        # 凝缩（放宽阈值）
        insights = self.consolidator.condense(min_cluster=2)
        dream_report["condensations"] = [i.insight_id for i in insights]

        # 提取模式
        procs = self.extract_procedural_memories()
        dream_report["new_procedural"] = [p.memory_id for p in procs]

        # 遗忘扫描
        dream_report["forget_scan"] = self.consolidator.forget_scan()

        return dream_report

    # ─────────────────────────────
    # 工具
    # ─────────────────────────────

    def _find_entry(self, memory_id: str):
        for e in self.storage.index.entries:
            if e.memory_id == memory_id:
                return e
        return None
