"""
Subconscious — 数据模型定义 (v1)

三种记忆类型 + 重要性加权 + 记忆索引 + whisper 格式。
所有模型均为普通 Python dataclass，不引入外部依赖，保持零开销兼容。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ──────────────────────────────────────────────
# 基础类型
# ──────────────────────────────────────────────

class MemoryType(str, Enum):
    EPISODIC = "episodic"    # 情景记忆：具体会话/事件
    SEMANTIC = "semantic"    # 语义记忆：概念/知识/规则
    PROCEDURAL = "procedural"  # 程序记忆：模式/技能/习惯


class RelationType(str, Enum):
    CAUSAL = "causal"        # 因果关联
    SIMILAR = "similar"      # 相似关联
    CONTRAST = "contrast"    # 对比关联
    TEMPORAL = "temporal"    # 时序关联
    SYMBOLIC = "symbolic"    # 符号化关联（凝缩产物）


class WhisperMode(str, Enum):
    WHISPER = "whisper"      # 默认：简短注入
    FULL = "full"            # 完整记忆摘要
    DREAM = "dream"          # 松散联想（空闲时）
    OFF = "off"              # 关闭


# ──────────────────────────────────────────────
# 重要性加权
# ──────────────────────────────────────────────

@dataclass
class ImportanceScore:
    """记忆重要性分数。"""
    base: float = 0.5           # 基础分，创建时设定
    frequency: float = 0.0     # 出现频率加分 [0–0.3]
    user_confirmed: float = 0.0  # 用户显式确认加分 [0–0.2]
    relevance: float = 0.0     # 与当前项目相关性 [0–0.3]
    pinned: bool = False       # 是否被固定（衰减暂停）

    # 元数据
    decay_rate: float = 0.05   # 每次未引用的衰减率
    last_referenced: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def total(self) -> float:
        """实时总分 = base + frequency + user_confirmed + relevance，上限 1.0。"""
        return min(1.0, self.base + self.frequency + self.user_confirmed + self.relevance)

    def decay(self) -> None:
        """执行一次衰减。pinned 时无效果。"""
        if self.pinned:
            return
        self.base = max(0.0, self.base - self.decay_rate)


# ──────────────────────────────────────────────
# 三种记忆类型
# ──────────────────────────────────────────────

@dataclass
class EpisodicMemory:
    """情景记忆 — 具体会话/事件。"""
    memory_id: str = field(default_factory=lambda: f"ep-{uuid.uuid4().hex[:12]}")
    memory_type: MemoryType = MemoryType.EPISODIC

    # 核心内容
    timestamp: datetime = field(default_factory=datetime.now)
    project: str = ""                     # 所属项目
    context: str = ""                     # 事件背景（一句话摘要）
    summary: str = ""                     # 详细描述
    key_decisions: list[str] = field(default_factory=list)   # 关键决策点
    outcome: str = ""                     # 结果/结论
    tags: list[str] = field(default_factory=list)

    # 关联
    related_episodic_ids: list[str] = field(default_factory=list)
    related_semantic_ids: list[str] = field(default_factory=list)
    related_procedural_ids: list[str] = field(default_factory=list)

    # 权重
    importance: ImportanceScore = field(default_factory=ImportanceScore)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __post_init__(self):
        if isinstance(self.importance, dict):
            self.importance = ImportanceScore(**self.importance)
        if isinstance(self.memory_type, str):
            self.memory_type = MemoryType(self.memory_type)
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)


@dataclass
class SemanticMemory:
    """语义记忆 — 抽象概念/知识/规则。"""
    memory_id: str = field(default_factory=lambda: f"se-{uuid.uuid4().hex[:12]}")
    memory_type: MemoryType = MemoryType.SEMANTIC

    # 核心内容
    concept: str = ""                     # 概念名称
    domain: str = ""                      # 所属领域
    definition: str = ""                  # 定义/描述
    examples: list[str] = field(default_factory=list)   # 实例速记
    tags: list[str] = field(default_factory=list)

    # 关联
    related_semantic_ids: list[str] = field(default_factory=list)
    source_episodic_ids: list[str] = field(default_factory=list)  # 来源情景

    # 权重
    importance: ImportanceScore = field(default_factory=ImportanceScore)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __post_init__(self):
        if isinstance(self.importance, dict):
            self.importance = ImportanceScore(**self.importance)
        if isinstance(self.memory_type, str):
            self.memory_type = MemoryType(self.memory_type)


@dataclass
class ProceduralMemory:
    """程序记忆 — 行为模式/习惯/技能。"""
    memory_id: str = field(default_factory=lambda: f"pr-{uuid.uuid4().hex[:12]}")
    memory_type: MemoryType = MemoryType.PROCEDURAL

    # 核心内容
    pattern_name: str = ""                # 模式名称
    trigger_conditions: list[str] = field(default_factory=list)  # 触发条件
    action_flow: list[str] = field(default_factory=list)         # 行动步骤
    frequency: int = 1                    # 已观察到的出现次数
    confidence: float = 0.3              # 模式置信度 [0–1]
    tags: list[str] = field(default_factory=list)

    # 关联
    source_episodic_ids: list[str] = field(default_factory=list)

    # 权重
    importance: ImportanceScore = field(default_factory=ImportanceScore)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __post_init__(self):
        if isinstance(self.importance, dict):
            self.importance = ImportanceScore(**self.importance)
        if isinstance(self.memory_type, str):
            self.memory_type = MemoryType(self.memory_type)


# ──────────────────────────────────────────────
# 关联与凝缩
# ──────────────────────────────────────────────

@dataclass
class MemoryRelation:
    """记忆间的关联关系。"""
    relation_id: str = field(default_factory=lambda: f"rl-{uuid.uuid4().hex[:8]}")
    source_id: str = ""
    target_id: str = ""
    relation_type: RelationType = RelationType.SIMILAR
    strength: float = 0.5                # 关联强度 [0–1]
    description: str = ""                 # 关联描述
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __post_init__(self):
        if isinstance(self.relation_type, str):
            self.relation_type = RelationType(self.relation_type)
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)


@dataclass
class CondensedInsight:
    """凝缩产物：由多个同类记忆压缩而成的抽象 insight。"""
    insight_id: str = field(default_factory=lambda: f"ci-{uuid.uuid4().hex[:8]}")
    source_ids: list[str] = field(default_factory=list)  # 被压缩的原始记忆 ID
    cluster_size: int = 0                 # 聚类数量
    abstraction: str = ""                 # 抽象描述
    implication: str = ""                 # 含义/指导意义
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)


# ──────────────────────────────────────────────
# Whisper
# ──────────────────────────────────────────────

@dataclass
class WhisperMessage:
    """潜意识 whisper 消息。"""
    source_memory_type: str = ""          # 来源记忆类型
    source_memory_id: str = ""            # 来源记忆 ID
    relation_description: str = ""        # 关联关系描述
    suggestion: str = ""                  # 可操作建议

    def format(self) -> str:
        return (
            "⚡ [subconscious whisper]\n"
            f"源：{self.source_memory_type}#{self.source_memory_id}\n"
            f"因：{self.relation_description}\n"
            f"提：{self.suggestion}"
        )


@dataclass
class WhisperPackage:
    """预注入包：在会话开始时加载。"""
    messages: list[WhisperMessage] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    max_messages: int = 3

    def add(self, msg: WhisperMessage) -> bool:
        if len(self.messages) >= self.max_messages:
            return False
        self.messages.append(msg)
        return True

    def is_empty(self) -> bool:
        return len(self.messages) == 0

    def format_all(self) -> str:
        if self.is_empty():
            return ""
        header = "── 潜意识 whisper ──\n"
        body = "\n\n".join(m.format() for m in self.messages)
        return header + body


# ──────────────────────────────────────────────
# 记忆索引
# ──────────────────────────────────────────────

@dataclass
class MemoryIndexEntry:
    """索引条目，用于快速查找。"""
    memory_id: str = ""
    memory_type: MemoryType = MemoryType.EPISODIC
    title: str = ""                       # 标题/摘要
    tags: list[str] = field(default_factory=list)
    importance_total: float = 0.0         # ImportanceScore.total 的快照
    timestamp: Optional[datetime] = None
    archived: bool = False

    def __post_init__(self):
        if isinstance(self.memory_type, str):
            self.memory_type = MemoryType(self.memory_type)
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)


@dataclass
class MemoryIndex:
    """记忆索引——顶层入口。"""
    entries: list[MemoryIndexEntry] = field(default_factory=list)
    relations: list[MemoryRelation] = field(default_factory=list)
    condensations: list[CondensedInsight] = field(default_factory=list)
    version: str = "1.0"
    updated_at: datetime = field(default_factory=datetime.now)
