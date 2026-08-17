"""
Conscious — 意识层接口

职责：
  - 响应用户命令 (/subconscious ...)
  - 管理潜意识层的状态（启动/关闭/查看）
  - 转发查询到前意识层（知识库）
  - 会话生命周期钩子（开始/结束）
"""

from __future__ import annotations

from typing import Any, Optional

from models.schemas import (
    WhisperMode, MemoryType, WhisperPackage,
)
from memory.storage import Storage
from .subconscious import SubconsciousPipeline
from .whisper import WhisperSystem


class Conscious:
    """意识层接口——供主会话调用的入口。"""

    def __init__(self, storage: Optional[Storage] = None):
        self.storage = storage or Storage()
        self.pipeline = SubconsciousPipeline(self.storage)
        self.whisper = WhisperSystem(pkg=self.storage.load_whisper_package())
        self._enabled = True

    # ─────────────────────────────
    # 命令处理
    # ─────────────────────────────

    def handle_command(self, command_line: str) -> str:
        """
        处理 /subconscious 命令。

        支持的子命令：
          status         → 查看潜意识状态
          recall <关键词> → 联想召回
          dream          → 触发梦境处理
          forget <id>    → 标记遗忘
          pin <id>       → 固定记忆
          off            → 关闭潜意识
          on             → 开启潜意识
          whisper        → 查看预注入包
          query <问题>   → 查询知识库
        """
        if not command_line.startswith("/subconscious"):
            return ""

        parts = command_line.strip().split(maxsplit=2)
        subcmd = parts[1] if len(parts) > 1 else "status"

        handlers = {
            "status": self._cmd_status,
            "recall": lambda: self._cmd_recall(parts[2] if len(parts) > 2 else ""),
            "dream": self._cmd_dream,
            "forget": lambda: self._cmd_forget(parts[2] if len(parts) > 2 else ""),
            "pin": lambda: self._cmd_pin(parts[2] if len(parts) > 2 else ""),
            "off": self._cmd_off,
            "on": self._cmd_on,
            "whisper": self._cmd_whisper,
        }

        handler = handlers.get(subcmd)
        if handler is None:
            return f"未知子命令: {subcmd}\n支持: status, recall, dream, forget, pin, off, on, whisper"

        return handler()

    # ─────────────────────────────
    # 命令实现
    # ─────────────────────────────

    def _cmd_status(self) -> str:
        """查看潜意识状态。"""
        stats = self.storage.stats()
        mode = self.whisper.current_mode()
        enabled = "开" if self._enabled else "关"

        lines = [
            "╔══ 潜意识状态 ══╗",
            f"  模式: {mode}",
            f"  状态: {enabled}",
            f"  总记忆: {stats['total_entries']} (活跃: {stats['active']}, 已归档: {stats['archived']})",
            f"  情景/语义/程序: {stats['by_type']['episodic']}/{stats['by_type']['semantic']}/{stats['by_type']['procedural']}",
            f"  关联关系: {stats['relations']}",
            f"  凝缩洞察: {stats['condensations']}",
            f"  平均重要性: {stats['avg_importance']:.2f}",
            "╚══ ══╝",
        ]
        return "\n".join(lines)

    def _cmd_recall(self, keyword: str) -> str:
        """联想召回：搜索记忆。"""
        if not keyword:
            return "用法: /subconscious recall <关键词>"

        results = self.storage.search(keyword)
        if not results:
            return f"未找到与「{keyword}」相关的记忆。"

        lines = [f"🔍 与「{keyword}」相关的记忆 ({len(results)} 条):"]
        for r in results[:10]:
            status = "📦" if r.archived else "📄"
            lines.append(f"  {status} [{r.memory_type.value}] {r.memory_id} — {r.title} (重要性: {r.importance_total:.2f})")
        return "\n".join(lines)

    def _cmd_dream(self) -> str:
        """触发梦境处理。"""
        report = self.pipeline.dream_process()
        lines = [
            "💭 梦境处理完成:",
            f"  新凝缩: {len(report['condensations'])}",
            f"  新模式: {len(report['new_procedural'])}",
            f"  归档: {report['forget_scan']['archived']}",
        ]
        return "\n".join(lines)

    def _cmd_forget(self, memory_id: str) -> str:
        """标记某记忆可遗忘（归档）。"""
        if not memory_id:
            return "用法: /subconscious forget <记忆ID>"
        self.storage.archive_memory(memory_id)
        return f"记忆 {memory_id} 已归档。"

    def _cmd_pin(self, memory_id: str) -> str:
        """固定某记忆防止衰减。"""
        if not memory_id:
            return "用法: /subconscious pin <记忆ID>"
        entry = self._find_entry(memory_id)
        if not entry:
            return f"未找到记忆: {memory_id}"
        mem = self._load_memory(entry)
        if mem and hasattr(mem, "importance"):
            mem.importance.pinned = True
            self._save_memory(mem)
            return f"记忆 {memory_id} 已固定，衰减暂停。"
        return f"无法固定记忆 {memory_id}。"

    def _cmd_off(self) -> str:
        """关闭潜意识层。"""
        self._enabled = False
        return "潜意识层已关闭（当前会话）。"

    def _cmd_on(self) -> str:
        """开启潜意识层。"""
        self._enabled = True
        return "潜意识层已开启。"

    def _cmd_whisper(self) -> str:
        """查看当前预注入包。"""
        pkg = self.storage.load_whisper_package()
        if pkg.is_empty():
            return "当前无预注入包。"
        return pkg.format_all()

    # ─────────────────────────────
    # 会话生命周期钩子
    # ─────────────────────────────

    def on_session_start(self) -> str:
        """
        会话开始时调用。
        返回 whisper 注入内容（空字符串 = 不注入）。
        """
        if not self._enabled:
            return ""

        pkg = self.storage.load_whisper_package()
        self.whisper = WhisperSystem(pkg=pkg)

        return self.whisper.get_injection()

    def on_session_end(self, transcript: str = "", project: str = "") -> dict[str, Any]:
        """
        会话结束时调用。
        执行完整潜意识管道处理。
        """
        if not self._enabled:
            return {"status": "skipped", "reason": "disabled"}

        result = self.pipeline.run(transcript=transcript, project=project)
        return result

    # ─────────────────────────────
    # 工具
    # ─────────────────────────────

    def _find_entry(self, memory_id: str):
        for e in self.storage.index.entries:
            if e.memory_id == memory_id:
                return e
        return None

    def _load_memory(self, entry):
        if entry.memory_type == MemoryType.EPISODIC:
            return self.storage.load_episodic(entry.memory_id)
        elif entry.memory_type == MemoryType.SEMANTIC:
            return self.storage.load_semantic(entry.memory_id)
        elif entry.memory_type == MemoryType.PROCEDURAL:
            return self.storage.load_procedural(entry.memory_id)
        return None

    def _save_memory(self, mem) -> None:
        from models.schemas import EpisodicMemory, SemanticMemory, ProceduralMemory
        if isinstance(mem, EpisodicMemory):
            self.storage.save_episodic(mem)
        elif isinstance(mem, SemanticMemory):
            self.storage.save_semantic(mem)
        elif isinstance(mem, ProceduralMemory):
            self.storage.save_procedural(mem)
