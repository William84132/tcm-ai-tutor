"""
模式识别规则 (Pattern Recognition)

定义可识别的行为模式模板——潜意识用来匹配"这种情况我见过"。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class PatternCategory(str, Enum):
    BUG_HUNT = "bug_hunt"               # 调试/修 Bug
    ARCH_DECISION = "arch_decision"     # 架构决策
    CODE_STYLE = "code_style"           # 编码风格
    PITFALL = "pitfall"                 # 反复踩坑
    WORKFLOW = "workflow"               # 工作流/操作习惯
    LEARNING = "learning"               # 学习新知识
    COMMUNICATION = "communication"     # 沟通模式


@dataclass
class PatternTemplate:
    """模式模板——定义一种可识别的行为模式。"""
    name: str
    category: PatternCategory
    description: str
    triggers: list[str] = field(default_factory=list)       # 触发关键词/信号
    min_occurrences: int = 3                                # 最少出现次数才确认模式
    weight: float = 0.3                                     # 模式的重要度基数


# ──────────────────────────────────────────────
# 预定义模式模板
# ──────────────────────────────────────────────

BUILTIN_PATTERNS: list[PatternTemplate] = [
    PatternTemplate(
        name="反复调试同一模块",
        category=PatternCategory.BUG_HUNT,
        description="用户连续多次调试同一个模块/函数，可能存在根源问题未解决",
        triggers=["不生效", "报错", "bug", "调试", "还是不对", "又出现"],
        min_occurrences=2,
        weight=0.6,
    ),
    PatternTemplate(
        name="架构决策缺乏记录",
        category=PatternCategory.ARCH_DECISION,
        description="用户做了一个重要的架构/技术选型但没有记录原因",
        triggers=["选型", "改用", "换成", "决定用", "迁移到"],
        min_occurrences=1,
        weight=0.5,
    ),
    PatternTemplate(
        name="重复踩坑",
        category=PatternCategory.PITFALL,
        description="用户在不同时间遇到相同的坑或错误",
        triggers=["又忘了", "又踩了", "又是这个", "老问题"],
        min_occurrences=2,
        weight=0.7,
    ),
    PatternTemplate(
        name="编码风格固化",
        category=PatternCategory.CODE_STYLE,
        description="用户反复使用类似代码模式，形成个人风格",
        triggers=["我喜欢", "我习惯", "我一直这样写"],
        min_occurrences=3,
        weight=0.3,
    ),
    PatternTemplate(
        name="学习新领域",
        category=PatternCategory.LEARNING,
        description="用户在接触不熟悉的技术栈或领域",
        triggers=["第一次用", "没接触过", "新手", "不熟", "了解下"],
        min_occurrences=1,
        weight=0.4,
    ),
]


def match_patterns(
    text: str,
    patterns: Optional[list[PatternTemplate]] = None,
) -> list[PatternTemplate]:
    """
    对文本进行模式匹配，返回命中的模式模板列表。

    简单的关键词匹配实现。
    """
    if patterns is None:
        patterns = BUILTIN_PATTERNS

    text_lower = text.lower()
    hits: list[PatternTemplate] = []
    for p in patterns:
        if any(trigger in text_lower for trigger in p.triggers):
            hits.append(p)
    return hits
