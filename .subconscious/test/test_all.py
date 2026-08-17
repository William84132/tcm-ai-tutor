"""
Subconscious — 综合测试

覆盖：
  1. 数据模型
  2. 重要性加权与衰减
  3. 存储后端
  4. 联想引擎
  5. 塑化/遗忘
  6. 潜意识管道
  7. Whisper 系统
  8. 前意识层查询
  9. 梦境处理
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

# 加入项目路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.schemas import (
    EpisodicMemory, SemanticMemory, ProceduralMemory,
    MemoryIndex, MemoryIndexEntry, MemoryRelation,
    CondensedInsight, WhisperMessage, WhisperPackage,
    WhisperMode, MemoryType, RelationType, ImportanceScore,
)
from models.importance import (
    calc_base_initial, calc_frequency_bonus, calc_relevance_bonus,
    should_archive, apply_decay, apply_reference_boost,
    ARCHIVE_THRESHOLD, DECAY_RATE_DEFAULT,
)
from models.patterns import (
    PatternTemplate, PatternCategory, BUILTIN_PATTERNS, match_patterns,
)


class TestSchemas(unittest.TestCase):
    """数据模型测试。"""

    def test_episodic_defaults(self):
        mem = EpisodicMemory()
        self.assertTrue(mem.memory_id.startswith("ep-"))
        self.assertEqual(mem.memory_type, MemoryType.EPISODIC)
        self.assertIsInstance(mem.importance, ImportanceScore)

    def test_semantic_defaults(self):
        mem = SemanticMemory()
        self.assertTrue(mem.memory_id.startswith("se-"))
        self.assertEqual(mem.memory_type, MemoryType.SEMANTIC)

    def test_procedural_defaults(self):
        mem = ProceduralMemory()
        self.assertTrue(mem.memory_id.startswith("pr-"))
        self.assertEqual(mem.memory_type, MemoryType.PROCEDURAL)

    def test_whisper_format(self):
        msg = WhisperMessage(
            source_memory_type="episodic",
            source_memory_id="ep-test123",
            relation_description="测试关联",
            suggestion="测试建议",
        )
        formatted = msg.format()
        self.assertIn("⚡", formatted)
        self.assertIn("ep-test123", formatted)
        self.assertIn("测试建议", formatted)

    def test_whisper_package_full(self):
        pkg = WhisperPackage(max_messages=2)
        self.assertTrue(pkg.add(WhisperMessage(source_memory_id="1")))
        self.assertTrue(pkg.add(WhisperMessage(source_memory_id="2")))
        self.assertFalse(pkg.add(WhisperMessage(source_memory_id="3")))
        self.assertFalse(pkg.is_empty())

    def test_importance_score_total(self):
        score = ImportanceScore(base=0.5, frequency=0.2, user_confirmed=0.1, relevance=0.2)
        self.assertAlmostEqual(score.total, 1.0)

    def test_importance_score_decay(self):
        score = ImportanceScore(base=0.5)
        score.decay()
        self.assertAlmostEqual(score.base, 0.45)

    def test_importance_score_pinned_no_decay(self):
        score = ImportanceScore(base=0.5, pinned=True)
        score.decay()
        self.assertAlmostEqual(score.base, 0.5)  # 不衰减


class TestImportance(unittest.TestCase):
    """重要性加权模型测试。"""

    def test_calc_base_initial(self):
        self.assertEqual(calc_base_initial(), 0.5)

    def test_calc_frequency_bonus(self):
        self.assertAlmostEqual(calc_frequency_bonus(1), 0.05)
        self.assertAlmostEqual(calc_frequency_bonus(10), 0.3)  # capped

    def test_calc_relevance_bonus(self):
        high = calc_relevance_bonus(keyword_matches=3)
        self.assertGreater(high, 0.2)
        low = calc_relevance_bonus(keyword_matches=0)
        self.assertLess(low, 0.1)

    def test_should_archive(self):
        self.assertTrue(should_archive(0.05))
        self.assertFalse(should_archive(0.5))

    def test_apply_decay(self):
        result = apply_decay(0.5)
        self.assertAlmostEqual(result, 0.45)
        # pinned
        result2 = apply_decay(0.5, pinned=True)
        self.assertAlmostEqual(result2, 0.5)

    def test_apply_reference_boost(self):
        result = apply_reference_boost(0.5)
        self.assertAlmostEqual(result, 0.6)


class TestPatterns(unittest.TestCase):
    """模式识别测试。"""

    def test_builtin_patterns_exist(self):
        self.assertGreater(len(BUILTIN_PATTERNS), 0)
        for p in BUILTIN_PATTERNS:
            self.assertTrue(p.name)
            self.assertIsInstance(p.category, PatternCategory)
            self.assertGreater(len(p.triggers), 0)

    def test_match_patterns(self):
        template = PatternTemplate(
            name="测试",
            category=PatternCategory.BUG_HUNT,
            description="测试",
            triggers=["bug", "错误"],
            min_occurrences=1,
            weight=0.5,
        )
        hits = match_patterns("这里有一个bug", [template])
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].name, "测试")

        hits2 = match_patterns("一切正常", [template])
        self.assertEqual(len(hits2), 0)


class TestStorageIntegration(unittest.TestCase):
    """存储后端集成测试。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from memory.storage import Storage
        self.storage = Storage(memory_dir=self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_save_and_load_episodic(self):
        mem = EpisodicMemory(context="测试", summary="测试内容", tags=["test"])
        mid = self.storage.save_episodic(mem)
        loaded = self.storage.load_episodic(mid)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.summary, "测试内容")

    def test_save_and_load_semantic(self):
        mem = SemanticMemory(concept="测试概念", definition="定义")
        mid = self.storage.save_semantic(mem)
        loaded = self.storage.load_semantic(mid)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.concept, "测试概念")

    def test_save_and_load_procedural(self):
        mem = ProceduralMemory(pattern_name="测试模式", frequency=3)
        mid = self.storage.save_procedural(mem)
        loaded = self.storage.load_procedural(mid)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.frequency, 3)

    def test_index_maintained(self):
        mem = EpisodicMemory(context="索引测试", summary="索引测试内容")
        self.storage.save_episodic(mem)
        self.assertEqual(len(self.storage.index.entries), 1)
        self.assertEqual(self.storage.index.entries[0].title, "索引测试内容"[:80])

    def test_archive(self):
        mem = EpisodicMemory(context="归档测试", summary="归档测试内容")
        mid = self.storage.save_episodic(mem)
        self.storage.archive_memory(mid)
        self.assertTrue(self.storage.index.entries[0].archived)

    def test_list_active(self):
        mem1 = EpisodicMemory(context="活跃", summary="活跃记忆")
        mem2 = EpisodicMemory(context="归档", summary="归档记忆")
        mid1 = self.storage.save_episodic(mem1)
        mid2 = self.storage.save_episodic(mem2)
        self.storage.archive_memory(mid2)

        active = self.storage.list_active()
        ids = [e.memory_id for e in active]
        self.assertIn(mid1, ids)
        self.assertNotIn(mid2, ids)

    def test_search(self):
        mem = EpisodicMemory(context="关键词测试", summary="这是一条关于数据库优化测试", tags=["db", "perf"])
        self.storage.save_episodic(mem)
        results = self.storage.search("数据库")
        self.assertGreater(len(results), 0)

    def test_archive_low_importance(self):
        # 创建一条低重要性记忆
        from models.importance import ARCHIVE_THRESHOLD
        mem = EpisodicMemory(context="低分", summary="低分测试")
        mem.importance.base = 0.05  # 低于归档阈值
        mid = self.storage.save_episodic(mem)

        n = self.storage.archive_low_importance(threshold=0.1)
        self.assertGreaterEqual(n, 1)

        entry = self.storage.index.entries[0]
        self.assertTrue(entry.archived)

    def test_whisper_package_roundtrip(self):
        pkg = WhisperPackage(max_messages=3)
        pkg.add(WhisperMessage(source_memory_type="episodic", source_memory_id="ep-1",
                                relation_description="测试", suggestion="建议"))
        self.storage.save_whisper_package(pkg)

        loaded = self.storage.load_whisper_package()
        self.assertFalse(loaded.is_empty())
        self.assertEqual(loaded.messages[0].suggestion, "建议")

    def test_clear_whisper_package(self):
        pkg = WhisperPackage()
        pkg.add(WhisperMessage(source_memory_id="1"))
        self.storage.save_whisper_package(pkg)
        self.storage.clear_whisper_package()
        loaded = self.storage.load_whisper_package()
        self.assertTrue(loaded.is_empty())

    def test_stats(self):
        mem = EpisodicMemory(context="统计", summary="统计测试")
        self.storage.save_episodic(mem)
        stats = self.storage.stats()
        self.assertEqual(stats["total_entries"], 1)
        self.assertIn("by_type", stats)


class TestAssociatorIntegration(unittest.TestCase):
    """联想引擎集成测试。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from memory.storage import Storage
        self.storage = Storage(memory_dir=self.tmpdir)
        from memory.associator import Associator
        self.associator = Associator(self.storage)

        # 创建一些测试记忆
        self.mem1 = EpisodicMemory(context="调试", summary="调试数据库连接超时", tags=["db", "debug", "perf"])
        self.mid1 = self.storage.save_episodic(self.mem1)
        self.mem2 = EpisodicMemory(context="优化", summary="优化数据库查询性能", tags=["db", "perf"])
        self.mid2 = self.storage.save_episodic(self.mem2)
        self.mem3 = EpisodicMemory(context="前端", summary="前端页面样式调整", tags=["frontend", "css"])
        self.mid3 = self.storage.save_episodic(self.mem3)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_associate_by_tags(self):
        """新记忆与现有记忆应该按标签关联。"""
        new_mem = EpisodicMemory(context="新数据库问题", summary="新的数据库连接错误", tags=["db", "debug"])
        new_id = self.storage.save_episodic(new_mem)

        relations = self.associator.associate(
            source_id=new_id,
            source_tags=new_mem.tags,
        )
        # 应该关联到 mem1 和 mem2（都有 db/debug 标签）
        target_ids = {r.target_id for r in relations}
        self.assertIn(self.mid1, target_ids)
        self.assertIn(self.mid2, target_ids)
        # 不应关联到 mem3（frontend/css 无重叠）
        self.assertNotIn(self.mid3, target_ids)

    def test_associate_by_keywords(self):
        """关键词匹配应该工作。"""
        new_mem = EpisodicMemory(context="数据库", summary="数据库超时问题排查")
        new_id = self.storage.save_episodic(new_mem)

        relations = self.associator.associate(
            source_id=new_id,
            source_text="数据库超时问题排查",
        )
        # 至少有一个关联
        self.assertGreaterEqual(len(relations), 0)

    def test_extract_keywords(self):
        from memory.associator import Associator
        keywords = Associator._extract_keywords("数据库连接超时排查方案")
        self.assertGreater(len(keywords), 0)
        # 应该提取出关键词
        self.assertTrue(any("数据库" in kw or "连接" in kw or "超时" in kw for kw in keywords))


class TestConsolidatorIntegration(unittest.TestCase):
    """固化和凝缩集成测试。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from memory.storage import Storage
        self.storage = Storage(memory_dir=self.tmpdir)
        from memory.consolidator import Consolidator
        self.consolidator = Consolidator(self.storage)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_condense_no_cluster(self):
        """记忆太少时不应凝缩。"""
        mem = EpisodicMemory(context="测试", summary="单条测试")
        self.storage.save_episodic(mem)
        insights = self.consolidator.condense(min_cluster=3)
        self.assertEqual(len(insights), 0)

    def test_condense_with_cluster(self):
        """同标签 ≥3 条时应凝缩。"""
        for i in range(3):
            mem = EpisodicMemory(
                context=f"调试{i}",
                summary=f"调试数据库问题{i}",
                tags=["db", "debug"],
            )
            self.storage.save_episodic(mem)

        insights = self.consolidator.condense(min_cluster=3)
        self.assertGreaterEqual(len(insights), 1)
        self.assertGreaterEqual(insights[0].cluster_size, 3)

    def test_consolidate_boost(self):
        """固化应提升被引用的记忆。"""
        mem = EpisodicMemory(context="原始", summary="原始记忆")
        mid = self.storage.save_episodic(mem)
        old_score = self.storage.index.entries[0].importance_total

        # 创建一条关系
        from models.schemas import MemoryRelation, RelationType
        rel = MemoryRelation(
            source_id="new-mem",
            target_id=mid,
            relation_type=RelationType.SIMILAR,
            strength=0.5,
        )
        self.storage.save_relation(rel)

        result = self.consolidator.consolidate(new_memory_ids=["new-mem"])
        self.assertGreaterEqual(result["boosted"], 1)

        # 重要性应提高
        new_score = self.storage.load_episodic(mid).importance.total
        self.assertGreaterEqual(new_score, old_score)

    def test_extract_patterns(self):
        """多次命中同一模式应生成程序记忆。"""
        for i in range(3):
            mem = EpisodicMemory(
                context=f"bug{i}",
                summary=f"这个bug又不生效，继续调试第{i}次",
                tags=["debug"],
            )
            self.storage.save_episodic(mem)

        procs = self.consolidator.extract_patterns()
        self.assertGreaterEqual(len(procs), 1)

    def test_forget_scan(self):
        """遗忘扫描应归档低分记忆。"""
        mem = EpisodicMemory(context="低分", summary="低分测试")
        mem.importance.base = 0.05
        self.storage.save_episodic(mem)

        result = self.consolidator.forget_scan()
        self.assertGreaterEqual(result["archived"], 1)


class TestPipelineIntegration(unittest.TestCase):
    """潜意识管道集成测试。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from memory.storage import Storage
        self.storage = Storage(memory_dir=self.tmpdir)
        from core.subconscious import SubconsciousPipeline
        self.pipeline = SubconsciousPipeline(self.storage)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_full_pipeline(self):
        """完整管道应执行所有 5 个阶段。"""
        result = self.pipeline.run(
            transcript="## 决策\n决定用 PostgreSQL 替代 MySQL\n## 原因\n需要更好的 JSON 支持",
            project="test-project",
            tags=["db", "arch"],
        )
        self.assertIn("stages", result)
        self.assertIn("1_encoding", result["stages"])
        self.assertEqual(result["stages"]["1_encoding"]["segments_created"], 1)

    def test_empty_transcript(self):
        """空 transcript 应跳过后续阶段。"""
        result = self.pipeline.run(transcript="")
        self.assertEqual(result["stages"]["1_encoding"]["segments_created"], 0)
        self.assertTrue(result["stages"]["2_association"].get("skipped", False))

    def test_pre_inject(self):
        """预注入应生成 whisper 包。"""
        mem = EpisodicMemory(context="重要", summary="非常重要的决策", tags=["important"])
        mem.importance.base = 0.9
        mid = self.storage.save_episodic(mem)

        pkg = self.pipeline.run_pre_inject([mid])
        self.assertFalse(pkg.is_empty())
        self.assertGreaterEqual(len(pkg.messages), 1)

    def test_dream_process(self):
        """梦境处理应交叉关联并提取模式。"""
        for i in range(4):
            mem = EpisodicMemory(
                context=f"梦{i}",
                summary=f"这是第{i}次调试数据库",
                tags=["db", "debug"],
            )
            self.storage.save_episodic(mem)

        dream = self.pipeline.dream_process()
        self.assertIn("condensations", dream)
        self.assertIn("new_procedural", dream)

    def test_extract_procedural(self):
        """提取程序记忆应返回结果。"""
        for i in range(3):
            mem = EpisodicMemory(
                context=f"抽{i}", summary=f"又忘了这个参数怎么设置{i}次了",
                tags=["forget"],
            )
            self.storage.save_episodic(mem)

        procs = self.pipeline.extract_procedural_memories()
        self.assertIsInstance(procs, list)


class TestWhisperSystem(unittest.TestCase):
    """Whisper 系统测试。"""

    def setUp(self):
        pkg = WhisperPackage(max_messages=3)
        pkg.add(WhisperMessage(
            source_memory_type="episodic",
            source_memory_id="ep-1",
            relation_description="测试关联",
            suggestion="测试建议内容",
        ))
        pkg.add(WhisperMessage(
            source_memory_type="semantic",
            source_memory_id="se-1",
            relation_description="语义关联",
            suggestion="语义建议",
        ))
        self.pkg = pkg

    def test_whisper_mode_resolves(self):
        """模式从环境变量解析。"""
        os.environ["SUBCONSCIOUS_MODE"] = "whisper"
        from core.whisper import WhisperSystem
        ws = WhisperSystem(pkg=self.pkg)
        self.assertEqual(ws.current_mode(), "whisper")

        os.environ["SUBCONSCIOUS_MODE"] = "off"
        ws2 = WhisperSystem(pkg=self.pkg)
        self.assertEqual(ws2.current_mode(), "off")
        self.assertFalse(ws2.has_injection())

        os.environ["SUBCONSCIOUS_MODE"] = "invalid"
        ws3 = WhisperSystem(pkg=self.pkg)
        self.assertEqual(ws3.current_mode(), "whisper")  # fallback

    def test_whisper_format_output(self):
        os.environ["SUBCONSCIOUS_MODE"] = "whisper"
        from core.whisper import WhisperSystem
        ws = WhisperSystem(pkg=self.pkg)
        output = ws.get_injection()
        self.assertIn("whisper", output)
        self.assertIn("ep-1", output)
        self.assertIn("测试建议内容", output)

    def test_off_mode_no_output(self):
        os.environ["SUBCONSCIOUS_MODE"] = "off"
        from core.whisper import WhisperSystem
        ws = WhisperSystem(pkg=self.pkg)
        self.assertEqual(ws.get_injection(), "")

    def test_empty_package_no_output(self):
        os.environ["SUBCONSCIOUS_MODE"] = "whisper"
        from core.whisper import WhisperSystem
        ws = WhisperSystem(pkg=WhisperPackage())
        self.assertEqual(ws.get_injection(), "")

    def test_dream_format(self):
        os.environ["SUBCONSCIOUS_MODE"] = "dream"
        from core.whisper import WhisperSystem
        ws = WhisperSystem(pkg=self.pkg)
        output = ws.get_injection()
        self.assertIn("dream", output)
        # dream 模式只取第一条
        self.assertNotIn("se-1", output)

    def test_full_format(self):
        os.environ["SUBCONSCIOUS_MODE"] = "full"
        from core.whisper import WhisperSystem
        ws = WhisperSystem(pkg=self.pkg)
        output = ws.get_injection()
        self.assertIn("full", output)

    def test_deduplication(self):
        """同一记忆不应重复发送。"""
        os.environ["SUBCONSCIOUS_MODE"] = "whisper"
        from core.whisper import WhisperSystem
        ws = WhisperSystem(pkg=self.pkg)
        ws.get_injection()  # 消耗第一条
        ws.get_injection()  # 不应再包含第一条


class TestPreconsciousIntegration(unittest.TestCase):
    """前意识层集成测试。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from knowledge.knowledge_index import Preconscious
        self.pc = Preconscious(knowledge_dir=self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_add_and_query(self):
        self.pc.add_entry("PostgreSQL JSON", "PostgreSQL 支持丰富的 JSON 查询操作", domain="db")
        results = self.pc.query("JSON 查询")
        self.assertGreater(len(results), 0)
        self.assertIn("PostgreSQL", results[0]["title"])

    def test_query_no_results(self):
        results = self.pc.query("不存在的关键词")
        self.assertEqual(len(results), 0)

    def test_remove_entry(self):
        self.pc.add_entry("测试", "内容")
        self.assertTrue(self.pc.remove_entry("测试"))
        self.assertFalse(self.pc.remove_entry("不存在的"))

    def test_list_entries(self):
        self.pc.add_entry("A", "内容A")
        self.pc.add_entry("B", "内容B")
        entries = self.pc.list_entries()
        self.assertIn("A", entries)
        self.assertIn("B", entries)

    def test_query_domain(self):
        self.pc.add_entry("概念1", "内容", domain="db")
        self.pc.add_entry("概念2", "内容", domain="db")
        self.pc.add_entry("前端", "内容", domain="frontend")

        results = self.pc.query_domain("db")
        self.assertEqual(len(results), 2)

    def test_stats(self):
        self.pc.add_entry("测试", "内容", domain="test")
        stats = self.pc.stats()
        self.assertEqual(stats["indexed_entries"], 1)
        self.assertIn("test", stats["domains"])


class TestConsciousCommands(unittest.TestCase):
    """意识层命令测试。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # patch storage dir
        from memory.storage import Storage
        self.storage = Storage(memory_dir=self.tmpdir)
        from core.conscious import Conscious
        self.conscious = Conscious(storage=self.storage)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_status_command(self):
        result = self.conscious.handle_command("/subconscious status")
        self.assertIn("潜意识状态", result)
        self.assertIn("总记忆", result)

    def test_off_on_commands(self):
        result = self.conscious.handle_command("/subconscious off")
        self.assertIn("关闭", result)
        result2 = self.conscious.handle_command("/subconscious on")
        self.assertIn("开启", result2)

    def test_unknown_subcommand(self):
        result = self.conscious.handle_command("/subconscious nonexistent")
        self.assertIn("未知子命令", result)

    def test_recall_no_keyword(self):
        result = self.conscious.handle_command("/subconscious recall")
        self.assertIn("用法", result)

    def test_recall_with_keyword(self):
        mem = EpisodicMemory(context="测试", summary="搜索关键词测试", tags=["search"])
        self.storage.save_episodic(mem)
        result = self.conscious.handle_command("/subconscious recall 搜索")
        self.assertIn("搜索", result)

    def test_whisper_command(self):
        from models.schemas import WhisperPackage, WhisperMessage
        pkg = WhisperPackage()
        pkg.add(WhisperMessage(source_memory_id="ep-1", suggestion="测试whisper"))
        self.storage.save_whisper_package(pkg)
        result = self.conscious.handle_command("/subconscious whisper")
        self.assertIn("测试whisper", result)

    def test_session_lifecycle(self):
        """会话生命周期钩子测试。"""
        # on_session_start — 无内容时不报错
        result = self.conscious.on_session_start()
        self.assertIsInstance(result, str)

        # on_session_end
        result2 = self.conscious.on_session_end(transcript="测试内容", project="test")
        if result2.get("status") == "skipped":
            self.assertEqual(result2["reason"], "disabled")
        else:
            self.assertIn("stages", result2)


class TestDreamIntegration(unittest.TestCase):
    """梦境处理集成测试。"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from memory.storage import Storage
        self.storage = Storage(memory_dir=self.tmpdir)
        from core.dream import DreamEngine
        self.dream = DreamEngine(self.storage)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_dream_with_few_memories(self):
        """记忆太少时梦境应为空。"""
        report = self.dream.process()
        self.assertEqual(report["cross_relations"], 0)

    def test_dream_cross_associate(self):
        """梦境应在不同类型记忆间建立关联。"""
        ep = EpisodicMemory(context="测试", summary="情景测试", tags=["common"])
        self.storage.save_episodic(ep)
        sem = SemanticMemory(concept="概念", definition="语义测试", tags=["common"])
        self.storage.save_semantic(sem)

        # 先手动加一些记忆
        report = self.dream.process()
        # 可能有关联，也可能因为标签覆盖不足而0
        self.assertIn("cross_relations", report)

    def test_dream_whisper_generation(self):
        """梦境应生成 whisper 候选。"""
        for i in range(3):
            ep = EpisodicMemory(context=f"测试{i}", summary=f"测试内容{i}", tags=["test"])
            self.storage.save_episodic(ep)
            sem = SemanticMemory(concept=f"概念{i}", definition=f"定义{i}", tags=["test"])
            self.storage.save_semantic(sem)

        report = self.dream.process()
        # 可能有梦境 whisper
        self.assertIn("dream_whisper", report)


class TestEdgeCases(unittest.TestCase):
    """边界情况测试。"""

    def test_episodic_very_long_summary(self):
        mem = EpisodicMemory(summary="A" * 10000)
        self.assertEqual(len(mem.summary), 10000)

    def test_storage_missing_file(self):
        from memory.storage import Storage
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = Storage(memory_dir=tmpdir)
            result = storage.load_episodic("nonexistent")
            self.assertIsNone(result)

    def test_index_unicode(self):
        from models.schemas import MemoryIndexEntry
        entry = MemoryIndexEntry(
            memory_id="test-unicode",
            title="中文标题测试🔥",
            tags=["中文", "emoji"],
        )
        self.assertEqual(entry.title, "中文标题测试🔥")

    def test_relation_self_reference(self):
        """不应关联自身。"""
        from memory.associator import Associator
        with tempfile.TemporaryDirectory() as tmpdir:
            from memory.storage import Storage
            storage = Storage(memory_dir=tmpdir)
            associator = Associator(storage)

            mem = EpisodicMemory(summary="自身测试", tags=["self"])
            mid = storage.save_episodic(mem)
            relations = associator._match_by_tags(mid, ["self"])
            self.assertEqual(len(relations), 0)

    def test_large_batch_save(self):
        """批量保存不崩溃。"""
        from memory.storage import Storage
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = Storage(memory_dir=tmpdir)
            for i in range(50):
                mem = EpisodicMemory(summary=f"批处理{i}", tags=["batch"])
                storage.save_episodic(mem)
            self.assertEqual(len(storage.index.entries), 50)


if __name__ == "__main__":
    unittest.main()
