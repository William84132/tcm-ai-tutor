"""
Consolidator — 记忆固化 + 凝缩 + 遗忘

职责：
  - Stage 3 凝缩 (Condensation)：同类记忆聚类 → 抽象 insight
  - Stage 4 固化 (Consolidation)：将处理后的记忆写入 + 重要性调整 + 归档
  - 遗忘机制：衰减、低分归档

与 encoder → associator → consolidator 串联使用。
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Optional

from models.schemas import (
    EpisodicMemory, SemanticMemory, ProceduralMemory,
    MemoryIndexEntry, CondensedInsight, MemoryType,
    ImportanceScore, MemoryRelation, RelationType,
)
from models.importance import (
    apply_decay, apply_reference_boost, calc_frequency_bonus,
    should_archive, ARCHIVE_THRESHOLD, DECAY_RATE_DEFAULT,
)
from models.patterns import PatternTemplate, BUILTIN_PATTERNS, match_patterns
from .storage import Storage


class Consolidator:
    """记忆固化 + 凝缩 + 遗忘。"""

    def __init__(self, storage: Storage):
        self.storage = storage

    # ─────────────────────────────
    # Stage 3: 凝缩 (Condensation)
    # ─────────────────────────────

    def condense(self, min_cluster: int = 3) -> list[CondensedInsight]:
        """
        对同类记忆执行凝缩——聚类 ≥ min_cluster 条的同类事件，压缩为抽象 insight。

        聚类策略：
          - 按标签重叠分组
          - 按同项目 + 时间窗口分组
          - 按关联关系强度分组

        Returns:
            本次新创建的凝缩洞察列表
        """
        active = self.storage.list_active()
        if len(active) < min_cluster:
            return []

        # 1) 按标签聚类
        tag_clusters = self._cluster_by_tags(active, min_cluster)
        # 2) 按关联关系聚类
        relation_clusters = self._cluster_by_relations(active, min_cluster)

        # 合并聚类结果
        all_clusters = tag_clusters + relation_clusters
        # 去重（按 ID 集合去重）
        seen: set[frozenset[str]] = set()
        insights: list[CondensedInsight] = []

        for cluster_ids in all_clusters:
            key = frozenset(cluster_ids)
            if key in seen:
                continue
            seen.add(key)

            # 加载实际内容用于抽象描述
            summaries = []
            for mid in cluster_ids:
                mem = self.storage.load_episodic(mid)
                if mem:
                    summaries.append(mem.summary[:200])
                else:
                    sem = self.storage.load_semantic(mid)
                    if sem:
                        summaries.append(sem.definition[:200])
                    else:
                        proc = self.storage.load_procedural(mid)
                        if proc:
                            summaries.append(f"[模式] {proc.pattern_name}")

            if not summaries:
                continue

            insight = CondensedInsight(
                source_ids=list(cluster_ids),
                cluster_size=len(cluster_ids),
                abstraction=self._generate_abstraction(summaries),
                implication=self._generate_implication(summaries),
            )
            self.storage.save_condensed(insight)
            insights.append(insight)

        return insights

    def _cluster_by_tags(self, entries: list[MemoryIndexEntry], min_size: int) -> list[list[str]]:
        """按标签重叠聚类。"""
        # 对每个标签收集记忆 ID
        tag_to_ids: dict[str, set[str]] = defaultdict(set)
        for e in entries:
            for tag in e.tags:
                tag_to_ids[tag].add(e.memory_id)

        clusters = []
        for tag, ids in tag_to_ids.items():
            if len(ids) >= min_size:
                clusters.append(list(ids))
        return clusters

    def _cluster_by_relations(self, entries: list[MemoryIndexEntry], min_size: int) -> list[list[str]]:
        """按关联关系聚类：找出互相之间有强关联的记忆群。"""
        # 构建邻接表
        adj: dict[str, set[str]] = defaultdict(set)
        for rel in self.storage.index.relations:
            if rel.strength >= 0.5:  # 只考虑强关联
                adj[rel.source_id].add(rel.target_id)
                adj[rel.target_id].add(rel.source_id)

        # DFS 找连通分量
        visited: set[str] = set()
        clusters = []
        for entry in entries:
            mid = entry.memory_id
            if mid in visited:
                continue
            component = self._dfs(mid, adj, visited)
            if len(component) >= min_size:
                clusters.append(list(component))
        return clusters

    @staticmethod
    def _dfs(node: str, adj: dict[str, set[str]], visited: set[str]) -> set[str]:
        """DFS 遍历找连通分量。"""
        stack = [node]
        component = set()
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            component.add(cur)
            for neighbor in adj.get(cur, set()):
                if neighbor not in visited:
                    stack.append(neighbor)
        return component

    @staticmethod
    def _generate_abstraction(summaries: list[str]) -> str:
        """从多个摘要生成一个抽象描述。"""
        # 简化实现：取前三段的共同主题
        if not summaries:
            return ""
        # 提取高频关键词作为抽象描述
        all_keywords = " ".join(summaries[:5])
        return f"[凝缩] {len(summaries)} 条同类记忆 — 主题: {all_keywords[:120]}..."

    @staticmethod
    def _generate_implication(summaries: list[str]) -> str:
        """生成含义/指导意义。"""
        count = len(summaries)
        if count >= 5:
            return f"该模式已出现 {count} 次，建议作为习惯性策略固化。"
        elif count >= 3:
            return f"该模式出现 {count} 次，值得关注。"
        return "模式识别中，需更多样本确认。"

    # ─────────────────────────────
    # Stage 4: 固化 (Consolidation)
    # ─────────────────────────────

    def consolidate(self, new_memory_ids: list[str]) -> dict:
        """
        执行固化流程：
          1. 更新被引用的记忆的重要性分数
          2. 对新记忆执行频率统计+加分
          3. 全局衰减
          4. 低分归档

        Args:
            new_memory_ids: 本轮新创建的记忆 ID 列表

        Returns:
            操作统计
        """
        result = {
            "boosted": 0,
            "decayed": 0,
            "archived": 0,
        }

        # 1) 被新记忆引用的现有记忆 → 加分
        for mid in new_memory_ids:
            relations = self.storage.get_relations(mid)
            for rel in relations:
                # 被引用的目标记忆加分
                target_id = rel.target_id if rel.source_id == mid else rel.source_id
                entry = self._find_entry(target_id)
                if entry and not entry.archived:
                    # 重新加载记忆更新 importance
                    mem = self._load_memory_by_entry(entry)
                    if mem and hasattr(mem, "importance") and hasattr(mem.importance, "base"):
                        old_base = mem.importance.base
                        mem.importance.base = apply_reference_boost(old_base)
                        # 也加频率分
                        mem.importance.frequency = calc_frequency_bonus(
                            self._count_references(entry.memory_id)
                        )
                        mem.importance.updated_at = datetime.now()
                        self._save_updated_memory(mem)
                        entry.importance_total = mem.importance.total
                        result["boosted"] += 1

        # 2) 全局衰减（除本轮新记忆外）
        for entry in self.storage.index.entries:
            if entry.memory_id in new_memory_ids or entry.archived:
                continue
            mem = self._load_memory_by_entry(entry)
            if mem and hasattr(mem, "importance") and hasattr(mem.importance, "base"):
                old_base = mem.importance.base
                mem.importance.base = apply_decay(
                    old_base,
                    pinned=mem.importance.pinned,
                    decay_rate=mem.importance.decay_rate,
                )
                # 频率分也随时间轻微衰减
                mem.importance.frequency = max(0.0, mem.importance.frequency - 0.01)
                mem.importance.updated_at = datetime.now()
                self._save_updated_memory(mem)
                entry.importance_total = mem.importance.total
                result["decayed"] += 1

        # 3) 检查归档
        result["archived"] = self.storage.archive_low_importance(ARCHIVE_THRESHOLD)

        self.storage._save_index()
        return result

    # ─────────────────────────────
    # 遗忘扫描 (Forgetting)
    # ─────────────────────────────

    def forget_scan(self) -> dict:
        """
        执行一次遗忘扫描：
          - Stage 3 的凝缩中丢弃的冗余标记
          - 低频低分的归档
          - 返回被遗忘/归档的统计
        """
        result = {
            "archived": 0,
            "condensed_this_round": 0,
        }

        # 尝试凝缩
        new_insights = self.condense(min_cluster=3)
        result["condensed_this_round"] = len(new_insights)

        # 归档低分记忆
        result["archived"] = self.storage.archive_low_importance(ARCHIVE_THRESHOLD)

        return result

    # ─────────────────────────────
    # 程序记忆生成 (Procedural Memory)
    # ─────────────────────────────

    def extract_patterns(
        self,
        patterns: Optional[list[PatternTemplate]] = None,
    ) -> list[ProceduralMemory]:
        """
        扫描活跃记忆，识别行为模式并生成程序记忆。

        当同一模式模板命中 ≥ min_occurrences 次时，创建一条程序记忆。
        """
        if patterns is None:
            patterns = BUILTIN_PATTERNS

        active = self.storage.list_active()
        found_patterns: list[ProceduralMemory] = []

        for template in patterns:
            # 统计该模式在活跃记忆中出现的频率
            match_count = 0
            source_ids: list[str] = []
            for entry in active:
                mem = self.storage.load_episodic(entry.memory_id)
                if mem and match_patterns(mem.summary, [template]):
                    match_count += 1
                    source_ids.append(entry.memory_id)

            if match_count >= template.min_occurrences:
                proc = ProceduralMemory(
                    pattern_name=template.name,
                    trigger_conditions=template.triggers,
                    frequency=match_count,
                    confidence=min(1.0, match_count / 10),
                    source_episodic_ids=source_ids,
                    tags=[template.category.value, "pattern"],
                    importance=ImportanceScore(
                        base=template.weight,
                        frequency=calc_frequency_bonus(match_count),
                    ),
                )
                self.storage.save_procedural(proc)
                found_patterns.append(proc)

        return found_patterns

    # ─────────────────────────────
    # 内部工具
    # ─────────────────────────────

    def _find_entry(self, memory_id: str) -> Optional[MemoryIndexEntry]:
        for e in self.storage.index.entries:
            if e.memory_id == memory_id:
                return e
        return None

    def _load_memory_by_entry(self, entry: MemoryIndexEntry):
        """根据索引条目加载对应的完整记忆对象。"""
        if entry.memory_type == MemoryType.EPISODIC:
            return self.storage.load_episodic(entry.memory_id)
        elif entry.memory_type == MemoryType.SEMANTIC:
            return self.storage.load_semantic(entry.memory_id)
        elif entry.memory_type == MemoryType.PROCEDURAL:
            return self.storage.load_procedural(entry.memory_id)
        return None

    def _save_updated_memory(self, mem) -> None:
        """保存更新后的记忆对象。"""
        if isinstance(mem, EpisodicMemory):
            self.storage.save_episodic(mem)
        elif isinstance(mem, SemanticMemory):
            self.storage.save_semantic(mem)
        elif isinstance(mem, ProceduralMemory):
            self.storage.save_procedural(mem)

    def _count_references(self, memory_id: str) -> int:
        """统计一条记忆被引用的次数。"""
        count = 0
        for rel in self.storage.index.relations:
            if rel.source_id == memory_id or rel.target_id == memory_id:
                count += 1
        return count
