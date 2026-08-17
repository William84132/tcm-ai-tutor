"""
Encoder — 记忆编码器

职责：将会话内容/文本 → 结构化记忆片段（EpisodicMemory）。
是潜意识处理管道的 Stage 1。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from models.schemas import EpisodicMemory, ImportanceScore
from models.importance import calc_base_initial


def encode_session(
    transcript: str,
    project: str = "",
    user_tags: Optional[list[str]] = None,
) -> list[EpisodicMemory]:
    """
    将会话文本编码为结构化情景记忆。

    这是简化版实现——提取关键决策点和摘要。
    后续 Phase 6 可接入 LLM 进行语义分析提取。

    Args:
        transcript: 会话文本（或关键事件摘要）
        project: 项目名称
        user_tags: 用户提供的标签

    Returns:
        EpisodicMemory 列表
    """
    lines = transcript.strip().split("\n")
    # 简单启发式分段：以空行或 Markdown 标题为界
    segments = _split_transcript(lines)

    memories: list[EpisodicMemory] = []
    for seg in segments:
        if len(seg.strip()) < 20:  # 太短的段忽略
            continue
        memory = EpisodicMemory(
            timestamp=datetime.now(),
            project=project,
            context=seg[:120].strip(),
            summary=seg[:500].strip(),
            key_decisions=_extract_decisions(seg),
            outcome=_extract_outcome(seg),
            tags=(user_tags or []) + _auto_tags(seg),
            importance=ImportanceScore(base=calc_base_initial()),
        )
        memories.append(memory)
    return memories


def encode_simple(
    context: str,
    summary: str,
    decisions: Optional[list[str]] = None,
    outcome: str = "",
    project: str = "",
    tags: Optional[list[str]] = None,
) -> EpisodicMemory:
    """
    直接创建一条情景记忆（无需 transcript 解析）。
    用于手动记录或非会话来源的记忆。
    """
    return EpisodicMemory(
        timestamp=datetime.now(),
        project=project,
        context=context,
        summary=summary,
        key_decisions=decisions or [],
        outcome=outcome,
        tags=tags or [],
        importance=ImportanceScore(base=calc_base_initial()),
    )


def _split_transcript(lines: list[str]) -> list[str]:
    """按空行或 Markdown h2/h3 分割。"""
    segments: list[str] = []
    current: list[str] = []
    for line in lines:
        if line.strip() == "" and current:
            segments.append("\n".join(current))
            current = []
        elif line.startswith("## ") or line.startswith("### "):
            if current:
                segments.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        segments.append("\n".join(current))
    return segments


def _extract_decisions(text: str) -> list[str]:
    """简单启发式提取决策点。"""
    decisions = []
    keywords = ["决定", "选择", "改用", "换成", "决定用",
                "选型", "采用", "弃用", "迁移"]
    for line in text.split("\n"):
        line_lower = line.lower()
        if any(kw in line_lower for kw in keywords):
            decisions.append(line.strip()[:200])
    return decisions


def _extract_outcome(text: str) -> str:
    """提取结论/结果。"""
    keywords = ["结论", "结果", "最终", "所以"]
    for line in text.split("\n"):
        line_lower = line.lower()
        if any(kw in line_lower for kw in keywords):
            return line.strip()[:300]
    return ""


def _auto_tags(text: str) -> list[str]:
    """自动打标签（基于关键词）。"""
    tag_map = {
        "debug": ["调试", "bug", "错误", "异常", "不生效", "报错"],
        "arch": ["架构", "设计模式", "重构", "选型"],
        "test": ["测试", "单元测试", "集成测试"],
        "deploy": ["部署", "上线", "CI", "CD"],
        "docs": ["文档", "README", "注释"],
        "security": ["安全", "权限", "认证", "加密"],
        "perf": ["性能", "优化", "延迟", "缓存"],
    }
    text_lower = text.lower()
    tags = []
    for tag, keywords in tag_map.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(tag)
    return tags
