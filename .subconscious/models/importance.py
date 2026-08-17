"""
重要性加权模型 (Importance Model)

控制记忆的生存周期——什么值得记住，什么该被遗忘。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional


# 权重系数 (可调)
WEIGHT_BASE_INITIAL = 0.5        # 新记忆初始基础分
WEIGHT_FREQUENCY_PER_OCCUR = 0.05  # 每次重复出现的加分
WEIGHT_FREQUENCY_CAP = 0.3       # 频率加分上限
WEIGHT_CONFIRMED = 0.15          # 用户显式确认加分
WEIGHT_RELEVANCE_HIGH = 0.3      # 高相关加分
WEIGHT_RELEVANCE_MED = 0.15      # 中相关加分
WEIGHT_RELEVANCE_LOW = 0.05      # 低相关加分

DECAY_RATE_DEFAULT = 0.05        # 默认每次衰减率
ARCHIVE_THRESHOLD = 0.1          # 归档阈值
BOOST_ON_REFERENCE = 0.1         # 被引用时的加分


def calc_base_initial() -> float:
    """新记忆初始基础分。"""
    return WEIGHT_BASE_INITIAL


def calc_frequency_bonus(count: int) -> float:
    """根据出现次数计算频率加分。"""
    bonus = count * WEIGHT_FREQUENCY_PER_OCCUR
    return min(WEIGHT_FREQUENCY_CAP, bonus)


def calc_relevance_bonus(
    keyword_matches: int = 0,
    project_overlap: bool = False,
    recent_days: Optional[int] = None,
) -> float:
    """
    计算相关性加分。

    Args:
        keyword_matches: 关键词匹配数
        project_overlap: 是否同项目
        recent_days: 距今天数，None 表示不检查时效
    """
    score = 0.0
    if keyword_matches >= 3:
        score += WEIGHT_RELEVANCE_HIGH
    elif keyword_matches >= 1:
        score += WEIGHT_RELEVANCE_MED
    else:
        score += WEIGHT_RELEVANCE_LOW

    if project_overlap:
        score += 0.1

    # 最近发生的记忆有额外加成
    if recent_days is not None and recent_days <= 7:
        score += 0.1

    return min(0.5, score)


def should_archive(total_score: float) -> bool:
    """判断是否应归档（低于阈值）。"""
    return total_score < ARCHIVE_THRESHOLD


def apply_decay(current_base: float, pinned: bool = False, decay_rate: float = DECAY_RATE_DEFAULT) -> float:
    """执行一次分数衰减。pinned 时无效果。"""
    if pinned:
        return current_base
    return max(0.0, current_base - decay_rate)


def apply_reference_boost(current_base: float) -> float:
    """被引用时的分数加成。"""
    return min(1.0, current_base + BOOST_ON_REFERENCE)
