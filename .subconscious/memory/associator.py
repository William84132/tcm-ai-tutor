"""
Associator — 联想引擎

职责：对新/旧记忆做语义匹配，建立关联关系图。
是潜意识处理管道的 Stage 2。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from models.schemas import (
    EpisodicMemory, SemanticMemory, ProceduralMemory,
    MemoryRelation, RelationType, MemoryIndexEntry,
)
from .storage import Storage


# 关联强度权重
WEIGHT_EXACT_TAG_MATCH = 0.8       # 标签完全匹配
WEIGHT_PARTIAL_TAG_MATCH = 0.5     # 标签部分重叠
WEIGHT_SAME_PROJECT = 0.6          # 同项目
WEIGHT_KEYWORD_MATCH = 0.4         # 关键词匹配
WEIGHT_WEAK = 0.2                  # 弱关联


@dataclass
class MatchResult:
    """一次匹配的结果。"""
    target_id: str
    relation_type: RelationType
    strength: float
    description: str


class Associator:
    """联想引擎。"""

    def __init__(self, storage: Storage):
        self.storage = storage

    # ─────────────────────────────
    # 主入口
    # ─────────────────────────────

    def associate(
        self,
        source_id: str,
        source_text: str = "",
        source_tags: Optional[list[str]] = None,
        source_project: str = "",
    ) -> list[MemoryRelation]:
        """
        对一条记忆执行联想——找到它和现有记忆的关联。

        Returns:
            新创建的关联关系列表
        """
        matches: list[MatchResult] = []

        # 按标签匹配
        if source_tags:
            matches.extend(self._match_by_tags(source_id, source_tags))

        # 按项目匹配
        if source_project:
            matches.extend(self._match_by_project(source_id, source_project))

        # 按关键词匹配
        if source_text:
            matches.extend(self._match_by_keywords(source_id, source_text))

        # 去重 + 合并相同目标
        merged = self._merge_matches(matches)

        # 保存关联
        relations = []
        for m in merged:
            relation = MemoryRelation(
                source_id=source_id,
                target_id=m.target_id,
                relation_type=m.relation_type,
                strength=m.strength,
                description=m.description,
            )
            self.storage.save_relation(relation)
            relations.append(relation)

        return relations

    # ─────────────────────────────
    # 匹配策略
    # ─────────────────────────────

    def _match_by_tags(self, source_id: str, tags: list[str]) -> list[MatchResult]:
        """标签匹配：找到有相同标签的记忆。"""
        results: list[MatchResult] = []
        tag_set = set(t.lower() for t in tags)

        for entry in self.storage.index.entries:
            if entry.memory_id == source_id or entry.archived:
                continue
            entry_tags = set(t.lower() for t in entry.tags)

            common = tag_set & entry_tags
            if not common:
                continue

            # 完全匹配 vs 部分匹配
            if tag_set == entry_tags:
                strength = WEIGHT_EXACT_TAG_MATCH
                desc = f"标签完全匹配: {', '.join(common)}"
            else:
                ratio = len(common) / max(len(tag_set), len(entry_tags))
                strength = WEIGHT_PARTIAL_TAG_MATCH * ratio
                desc = f"标签重叠: {', '.join(common)}"

            results.append(MatchResult(
                target_id=entry.memory_id,
                relation_type=RelationType.SIMILAR,
                strength=round(strength, 2),
                description=desc,
            ))

        return results

    def _match_by_project(self, source_id: str, project: str) -> list[MatchResult]:
        """项目匹配：同项目的记忆倾向于关联。"""
        results: list[MatchResult] = []
        project_lower = project.lower()

        for entry in self.storage.index.entries:
            if entry.memory_id == source_id or entry.archived:
                continue
            # 只有需要载入实际内容才能拿到 project 字段，这里简化处理
            # 通过 entry.title 判断
            if project_lower in entry.title.lower():
                results.append(MatchResult(
                    target_id=entry.memory_id,
                    relation_type=RelationType.TEMPORAL,
                    strength=WEIGHT_SAME_PROJECT,
                    description=f"同项目: {project}",
                ))

        return results

    def _match_by_keywords(self, source_id: str, text: str) -> list[MatchResult]:
        """关键词匹配：提取文本关键词，匹配标题和标签。"""
        keywords = self._extract_keywords(text)
        if not keywords:
            return []

        results: list[MatchResult] = []
        for entry in self.storage.index.entries:
            if entry.memory_id == source_id or entry.archived:
                continue

            match_count = 0
            for kw in keywords:
                if kw in entry.title.lower():
                    match_count += 1
                elif any(kw in tag.lower() for tag in entry.tags):
                    match_count += 1

            if match_count == 0:
                continue

            strength = min(WEIGHT_KEYWORD_MATCH, WEIGHT_KEYWORD_MATCH * (match_count / max(len(keywords), 1)))
            results.append(MatchResult(
                target_id=entry.memory_id,
                relation_type=RelationType.SIMILAR,
                strength=round(strength, 2),
                description=f"关键词匹配 ({match_count} hits)",
            ))

        return results

    # ─────────────────────────────
    # 工具方法
    # ─────────────────────────────

    @staticmethod
    def _extract_keywords(text: str, max_keywords: int = 10) -> list[str]:
        """从文本中提取关键词（分词+去停用词）。"""
        # 中文分词（简单按字/词切分）
        # 去掉常见停用词
        stop_words = {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "你", "会", "着", "没有", "看", "好", "自己", "这", "他", "她",
            "它", "们", "那", "些", "来", "把", "被", "让", "给", "为",
            "所", "以", "能", "下", "过", "但", "而", "或", "与", "及",
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "can", "could", "shall", "should", "may", "might",
            "this", "that", "these", "those", "it", "its", "it's",
        }

        # 按非字母数字分割（保留中文）
        tokens = re.findall(r'[a-zA-Z]+|[一-龥]+', text.lower())
        # 过滤停用词 + 太短的词
        tokens = [t for t in tokens if len(t) >= 2 and t not in stop_words]

        # 按出现频次排序取 top N
        freq = {}
        for t in tokens:
            freq[t] = freq.get(t, 0) + 1
        sorted_tokens = sorted(freq.items(), key=lambda x: -x[1])
        return [t for t, _ in sorted_tokens[:max_keywords]]

    @staticmethod
    def _merge_matches(matches: list[MatchResult]) -> list[MatchResult]:
        """合并指向同一目标的多个匹配结果（取最高强度）。"""
        best: dict[str, MatchResult] = {}
        for m in matches:
            if m.target_id not in best or m.strength > best[m.target_id].strength:
                best[m.target_id] = m
        return list(best.values())
