"""
Preconscious — 前意识层接口

职责：
  - 为意识层提供静态知识查询
  - 接入外部数据库/文档/API 文档
  - 管理知识索引

前意识层与潜意识层的核心区别：
  前意识：死的、按需查询的、意识层直接调用的
  潜意识：活的、持续处理的、通过 whisper 间接影响的
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional


# 默认知识库路径
ENV_KNOWLEDGE_DIR = "SUBCONSCIOUS_KNOWLEDGE_DIR"
DEFAULT_KNOWLEDGE_DIR = Path.cwd() / "knowledge"


class Preconscious:
    """前意识层——知识库接入接口。"""

    def __init__(self, knowledge_dir: Optional[str] = None):
        dir_str = knowledge_dir or os.environ.get(ENV_KNOWLEDGE_DIR) or str(DEFAULT_KNOWLEDGE_DIR)
        self.knowledge_dir = Path(dir_str)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

        self._index: dict[str, dict] = {}
        self._load_index()

    # ─────────────────────────────
    # 索引管理
    # ─────────────────────────────

    def _index_path(self) -> Path:
        return self.knowledge_dir / "knowledge_index.json"

    def _load_index(self) -> None:
        path = self._index_path()
        if path.exists():
            try:
                self._index = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, FileNotFoundError):
                self._index = {}

    def _save_index(self) -> None:
        self._index_path().write_text(
            json.dumps(self._index, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    # ─────────────────────────────
    # 查询接口
    # ─────────────────────────────

    def query(self, question: str, source: str = "all", top_k: int = 5) -> list[dict[str, Any]]:
        """
        查询知识库。返回匹配的知识条目。

        Args:
            question: 查询文本
            source: 数据源筛选（"all" 或指定源名称）
            top_k: 返回最大条数

        Returns:
            匹配的知识条目列表，每项含 {source, title, content, score}
        """
        results: list[dict[str, Any]] = []

        # 1) 自建知识索引
        keyword_lower = question.lower()
        for name, entry in self._index.items():
            if source != "all" and entry.get("source", "") != source:
                continue
            # 简单关键词匹配
            title = entry.get("title", "")
            content = entry.get("content", "")
            if keyword_lower in title.lower() or keyword_lower in content.lower():
                results.append({
                    "source": entry.get("source", "local"),
                    "title": title,
                    "content": content[:500],
                    "score": 0.8,
                })

        # 2) 文件扫描（知识目录下的 markdown/csv/json 文件）
        if len(results) < top_k:
            results.extend(self._scan_files(question, source))

        # 排序取 top_k
        results.sort(key=lambda r: r.get("score", 0), reverse=True)
        return results[:top_k]

    def query_domain(self, domain: str) -> list[dict[str, Any]]:
        """按领域查询知识。"""
        results = []
        for name, entry in self._index.items():
            if entry.get("domain", "") == domain:
                results.append({
                    "source": entry.get("source", "local"),
                    "title": entry.get("title", name),
                    "content": entry.get("content", "")[:500],
                    "score": 1.0,
                })
        return results

    def _scan_files(self, keyword: str, source: str) -> list[dict[str, Any]]:
        """扫描知识目录下的文件，做简单关键词匹配。"""
        results: list[dict[str, Any]] = []
        if not self.knowledge_dir.exists():
            return results

        keyword_lower = keyword.lower()
        for fpath in self.knowledge_dir.rglob("*.md"):
            if source != "all" and not fpath.name.startswith(source):
                continue
            try:
                text = fpath.read_text(encoding="utf-8", errors="ignore")
                if keyword_lower in text.lower():
                    # 找到匹配行的前后文
                    lines = text.split("\n")
                    for i, line in enumerate(lines):
                        if keyword_lower in line.lower():
                            start = max(0, i - 2)
                            end = min(len(lines), i + 3)
                            snippet = "\n".join(lines[start:end])
                            results.append({
                                "source": "file",
                                "title": fpath.relative_to(self.knowledge_dir).as_posix(),
                                "content": snippet[:500],
                                "score": 0.5,
                            })
                            break
            except Exception:
                continue

        return results

    # ─────────────────────────────
    # 条目管理
    # ─────────────────────────────

    def add_entry(self, name: str, content: str, source: str = "manual", domain: str = "", tags: Optional[list[str]] = None) -> None:
        """向知识索引添加一条知识。"""
        self._index[name] = {
            "source": source,
            "domain": domain,
            "title": name,
            "content": content,
            "tags": tags or [],
        }
        self._save_index()

    def remove_entry(self, name: str) -> bool:
        """从知识索引移除一条知识。"""
        if name in self._index:
            del self._index[name]
            self._save_index()
            return True
        return False

    def list_entries(self) -> list[str]:
        """列出所有知识索引条目的名称。"""
        return list(self._index.keys())

    def stats(self) -> dict[str, Any]:
        return {
            "indexed_entries": len(self._index),
            "knowledge_dir": str(self.knowledge_dir),
            "domains": list(set(e.get("domain", "unknown") for e in self._index.values())),
        }
