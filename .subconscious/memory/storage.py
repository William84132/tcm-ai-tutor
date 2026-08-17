"""
Storage — 记忆存储后端

职责：文件 I/O、记忆索引管理、存档/恢复。
所有记忆持久化在 .claude/memory/ 目录，与 Claude Code 原生 memory 兼容格式。
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

from models.schemas import (
    EpisodicMemory, SemanticMemory, ProceduralMemory,
    MemoryIndex, MemoryIndexEntry, MemoryRelation,
    CondensedInsight, WhisperPackage, MemoryType,
)


# 默认路径（可用 SUBCONSCIOUS_MEMORY_DIR 环境变量覆盖）
DEFAULT_MEMORY_DIR = Path(
    os.environ.get("SUBCONSCIOUS_MEMORY_DIR")
    or (Path.home() / ".dsh" / "subconscious-memory")
)
INDEX_FILENAME = "memory_index.json"
WHISPER_FILENAME = "whisper_package.json"


class Storage:
    """记忆存储后端。"""

    def __init__(self, memory_dir: Optional[Union[str, Path]] = None):
        self.memory_dir = Path(memory_dir) if memory_dir else DEFAULT_MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self._index_path = self.memory_dir / INDEX_FILENAME
        self._whisper_path = self.memory_dir / WHISPER_FILENAME

        # 按类型分目录
        self._episodic_dir = self.memory_dir / "episodic"
        self._semantic_dir = self.memory_dir / "semantic"
        self._procedural_dir = self.memory_dir / "procedural"
        self._condensed_dir = self.memory_dir / "condensed"
        for d in [self._episodic_dir, self._semantic_dir,
                  self._procedural_dir, self._condensed_dir]:
            d.mkdir(exist_ok=True)

        # 加载索引
        self.index = self._load_index()

    # ─────────────────────────────
    # 索引管理
    # ─────────────────────────────

    def _load_index(self) -> MemoryIndex:
        if self._index_path.exists():
            try:
                data = json.loads(self._index_path.read_text(encoding="utf-8"))
                return MemoryIndex(
                    entries=[MemoryIndexEntry(**e) for e in data.get("entries", [])],
                    relations=[MemoryRelation(**r) for r in data.get("relations", [])],
                    condensations=[CondensedInsight(**c) for c in data.get("condensations", [])],
                    version=data.get("version", "1.0"),
                    updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
                )
            except (json.JSONDecodeError, KeyError):
                pass
        return MemoryIndex()

    def _save_index(self) -> None:
        self.index.updated_at = datetime.now()
        data = {
            "entries": [self._to_json(e) for e in self.index.entries],
            "relations": [r.to_dict() for r in self.index.relations],
            "condensations": [c.to_dict() for c in self.index.condensations],
            "version": self.index.version,
            "updated_at": self.index.updated_at.isoformat(),
        }
        self._index_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    @staticmethod
    def _to_json(obj: Any) -> dict:
        if isinstance(obj, MemoryIndexEntry):
            d = {
                "memory_id": obj.memory_id,
                "memory_type": obj.memory_type.value if isinstance(obj.memory_type, MemoryType) else obj.memory_type,
                "title": obj.title,
                "tags": obj.tags,
                "importance_total": obj.importance_total,
                "timestamp": obj.timestamp.isoformat() if obj.timestamp else None,
                "archived": obj.archived,
            }
            return d
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if hasattr(obj, "dict"):
            return obj.dict()
        if hasattr(obj, "__dict__"):
            return {k: v.isoformat() if isinstance(v, datetime) else v
                    for k, v in obj.__dict__.items() if not k.startswith("_")}
        return dict(obj)

    # ─────────────────────────────
    # 记忆存取
    # ─────────────────────────────

    def save_episodic(self, memory: EpisodicMemory) -> str:
        """保存一条情景记忆，返回 memory_id。"""
        filepath = self._episodic_dir / f"{memory.memory_id}.json"
        filepath.write_text(
            json.dumps(memory.to_dict(), ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        self._upsert_index_entry(
            MemoryIndexEntry(
                memory_id=memory.memory_id,
                memory_type=MemoryType.EPISODIC,
                title=memory.summary[:80],
                tags=memory.tags,
                importance_total=memory.importance.total,
                timestamp=memory.timestamp,
                archived=False,
            )
        )
        return memory.memory_id

    def save_semantic(self, memory: SemanticMemory) -> str:
        """保存一条语义记忆。"""
        filepath = self._semantic_dir / f"{memory.memory_id}.json"
        filepath.write_text(
            json.dumps(memory.to_dict(), ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        self._upsert_index_entry(
            MemoryIndexEntry(
                memory_id=memory.memory_id,
                memory_type=MemoryType.SEMANTIC,
                title=memory.concept,
                tags=memory.tags,
                importance_total=memory.importance.total,
                timestamp=None,
                archived=False,
            )
        )
        return memory.memory_id

    def save_procedural(self, memory: ProceduralMemory) -> str:
        """保存一条程序记忆。"""
        filepath = self._procedural_dir / f"{memory.memory_id}.json"
        filepath.write_text(
            json.dumps(memory.to_dict(), ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        self._upsert_index_entry(
            MemoryIndexEntry(
                memory_id=memory.memory_id,
                memory_type=MemoryType.PROCEDURAL,
                title=memory.pattern_name,
                tags=memory.tags,
                importance_total=memory.importance.total,
                timestamp=None,
                archived=False,
            )
        )
        return memory.memory_id

    def load_episodic(self, memory_id: str) -> Optional[EpisodicMemory]:
        filepath = self._episodic_dir / f"{memory_id}.json"
        if not filepath.exists():
            return None
        data = json.loads(filepath.read_text(encoding="utf-8"))
        return EpisodicMemory(**data)

    def load_semantic(self, memory_id: str) -> Optional[SemanticMemory]:
        filepath = self._semantic_dir / f"{memory_id}.json"
        if not filepath.exists():
            return None
        data = json.loads(filepath.read_text(encoding="utf-8"))
        return SemanticMemory(**data)

    def load_procedural(self, memory_id: str) -> Optional[ProceduralMemory]:
        filepath = self._procedural_dir / f"{memory_id}.json"
        if not filepath.exists():
            return None
        data = json.loads(filepath.read_text(encoding="utf-8"))
        return ProceduralMemory(**data)

    def _upsert_index_entry(self, entry: MemoryIndexEntry) -> None:
        for i, e in enumerate(self.index.entries):
            if e.memory_id == entry.memory_id:
                self.index.entries[i] = entry
                self._save_index()
                return
        self.index.entries.append(entry)
        self._save_index()

    # ─────────────────────────────
    # 关联管理
    # ─────────────────────────────

    def save_relation(self, relation: MemoryRelation) -> None:
        """保存一条关联关系。"""
        # 去重更新
        for i, r in enumerate(self.index.relations):
            if (r.source_id == relation.source_id
                    and r.target_id == relation.target_id
                    and r.relation_type == relation.relation_type):
                self.index.relations[i] = relation
                self._save_index()
                return
        self.index.relations.append(relation)
        self._save_index()

    def get_relations(self, memory_id: str) -> list[MemoryRelation]:
        """获取一条记忆的所有关联。"""
        return [
            r for r in self.index.relations
            if r.source_id == memory_id or r.target_id == memory_id
        ]

    # ─────────────────────────────
    # 凝缩管理
    # ─────────────────────────────

    def save_condensed(self, insight: CondensedInsight) -> None:
        self.index.condensations.append(insight)
        self._save_index()

    # ─────────────────────────────
    # 存档/恢复
    # ─────────────────────────────

    def archive_memory(self, memory_id: str) -> None:
        """将一条记忆标记为存档（不删除文件）。"""
        for entry in self.index.entries:
            if entry.memory_id == memory_id:
                entry.archived = True
                self._save_index()
                return

    def archive_low_importance(self, threshold: float = 0.1) -> int:
        """归档所有低于阈值的记忆。返回归档数量。"""
        count = 0
        for entry in self.index.entries:
            if not entry.archived and entry.importance_total < threshold:
                entry.archived = True
                count += 1
        if count:
            self._save_index()
        return count

    def list_active(self, memory_type: Optional[MemoryType] = None) -> list[MemoryIndexEntry]:
        """列出所有活跃（未归档）的记忆。"""
        results = [e for e in self.index.entries if not e.archived]
        if memory_type:
            results = [e for e in results if e.memory_type == memory_type]
        return sorted(results, key=lambda e: e.importance_total, reverse=True)

    def search(self, keyword: str) -> list[MemoryIndexEntry]:
        """关键词搜索（基于索引 title + tags 的简单文本匹配）。"""
        keyword_lower = keyword.lower()
        hits = []
        for entry in self.index.entries:
            if keyword_lower in entry.title.lower():
                hits.append(entry)
                continue
            if any(keyword_lower in tag.lower() for tag in entry.tags):
                hits.append(entry)
                continue
        return hits

    # ─────────────────────────────
    # Whisper 包
    # ─────────────────────────────

    def save_whisper_package(self, pkg: WhisperPackage) -> None:
        data = {
            "messages": [m.__dict__ for m in pkg.messages],
            "generated_at": pkg.generated_at.isoformat(),
            "max_messages": pkg.max_messages,
        }
        self._whisper_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    def load_whisper_package(self) -> WhisperPackage:
        if not self._whisper_path.exists():
            return WhisperPackage()
        try:
            data = json.loads(self._whisper_path.read_text(encoding="utf-8"))
            from models.schemas import WhisperMessage
            return WhisperPackage(
                messages=[WhisperMessage(**m) for m in data.get("messages", [])],
                generated_at=datetime.fromisoformat(data["generated_at"]) if "generated_at" in data else datetime.now(),
                max_messages=data.get("max_messages", 3),
            )
        except (json.JSONDecodeError, KeyError):
            return WhisperPackage()

    def clear_whisper_package(self) -> None:
        if self._whisper_path.exists():
            self._whisper_path.unlink()

    # ─────────────────────────────
    # 数据统计
    # ─────────────────────────────

    def stats(self) -> dict[str, Any]:
        return {
            "total_entries": len(self.index.entries),
            "active": len([e for e in self.index.entries if not e.archived]),
            "archived": len([e for e in self.index.entries if e.archived]),
            "relations": len(self.index.relations),
            "condensations": len(self.index.condensations),
            "by_type": {
                "episodic": len([e for e in self.index.entries if e.memory_type == MemoryType.EPISODIC]),
                "semantic": len([e for e in self.index.entries if e.memory_type == MemoryType.SEMANTIC]),
                "procedural": len([e for e in self.index.entries if e.memory_type == MemoryType.PROCEDURAL]),
            },
            "avg_importance": (
                sum(e.importance_total for e in self.index.entries if not e.archived)
                / max(1, len([e for e in self.index.entries if not e.archived]))
            ),
        }
