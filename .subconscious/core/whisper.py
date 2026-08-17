"""
Whisper — 潜意识 whisper 系统

职责：
  - 从预注入包读取 whisper 消息
  - 控制注入时机与频率（whisper / full / dream / off）
  - 格式化输出

核心原则：话痨是潜意识的天敌。沉默好过噪音。
"""

from __future__ import annotations

import os
from typing import Optional

from models.schemas import (
    WhisperMessage, WhisperPackage, WhisperMode,
)


# 环境变量配置
ENV_MODE = "SUBCONSCIOUS_MODE"
ENV_CONFIRM = "SUBCONSCIOUS_CONFIRM_REQUIRED"

# 行为约束
MAX_WHISPER_LENGTH = 80           # 单条 whisper 最大字数
MAX_WHISPER_COUNT = 3             # whisper 模式最大条数
MAX_FULL_LENGTH = 2000            # full 模式最大长度


class WhisperSystem:
    """Whisper 输出控制器。"""

    def __init__(self, pkg: Optional[WhisperPackage] = None):
        self.pkg = pkg or WhisperPackage()
        self.mode = self._resolve_mode()
        self._history: set[str] = set()  # 已发送过的记忆 ID，避免重复

    # ─────────────────────────────
    # 模式解析
    # ─────────────────────────────

    @staticmethod
    def _resolve_mode() -> WhisperMode:
        """从环境变量解析注入模式。"""
        mode_str = os.environ.get(ENV_MODE, "whisper").strip().lower()
        for mode in WhisperMode:
            if mode.value == mode_str:
                return mode
        return WhisperMode.WHISPER

    # ─────────────────────────────
    # 入口
    # ─────────────────────────────

    def get_injection(self) -> str:
        """
        获取当前应注入的内容。

        Returns:
            格式化后的注入文本（空字符串表示不注入）
        """
        if self.mode == WhisperMode.OFF:
            return ""
        if self.pkg.is_empty():
            return ""

        if self.mode == WhisperMode.WHISPER:
            return self._format_whisper()
        elif self.mode == WhisperMode.FULL:
            return self._format_full()
        elif self.mode == WhisperMode.DREAM:
            return self._format_dream()
        return ""

    # ─────────────────────────────
    # 格式工厂
    # ─────────────────────────────

    def _format_whisper(self) -> str:
        """whisper 模式：简短注入。"""
        messages = self._select_messages(min(len(self.pkg.messages), MAX_WHISPER_COUNT))
        if not messages:
            return ""
        parts = ["── 潜意识 whisper ──"]
        for m in messages:
            parts.append(m.format())
            self._history.add(m.source_memory_id)
        body = "\n\n".join(parts)
        return body

    def _format_full(self) -> str:
        """full 模式：完整记忆摘要。"""
        if not self.pkg.messages:
            return ""

        # 将所有消息转为完整文本
        lines = ["── 潜意识报告 (full) ──"]
        char_count = 0
        for m in self.pkg.messages:
            text = m.format()
            if char_count + len(text) > MAX_FULL_LENGTH:
                break
            lines.append(text)
            lines.append("---")
            char_count += len(text)
            self._history.add(m.source_memory_id)

        body = "\n\n".join(lines)
        return body

    def _format_dream(self) -> str:
        """dream 模式：松散联想，只取第一条。"""
        if not self.pkg.messages:
            return ""

        msg = self.pkg.messages[0]
        text = (
            "💭 [subconscious dream]\n"
            f"{msg.source_memory_type}#{msg.source_memory_id}\n"
            f"💡 {msg.suggestion[:MAX_WHISPER_LENGTH]}"
        )
        self._history.add(msg.source_memory_id)
        return text

    # ─────────────────────────────
    # 选择策略
    # ─────────────────────────────

    def _select_messages(self, count: int) -> list[WhisperMessage]:
        """从包中选择要发送的消息（去重 + 排序）。"""
        # 过滤已发送过的
        candidates = [
            m for m in self.pkg.messages
            if m.source_memory_id not in self._history
        ]
        return candidates[:count]

    # ─────────────────────────────
    # 状态
    # ─────────────────────────────

    def has_injection(self) -> bool:
        """检查是否存在可注入内容。"""
        if self.mode == WhisperMode.OFF:
            return False
        if self.pkg.is_empty():
            return False
        return any(m.source_memory_id not in self._history for m in self.pkg.messages)

    def current_mode(self) -> str:
        return self.mode.value

    @staticmethod
    def format_standalone(msg: WhisperMessage) -> str:
        """格式化单条 whisper 为可输出文本。"""
        return msg.format()
