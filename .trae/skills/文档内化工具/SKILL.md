---
name: 文档内化工具
description: "文档内化工具。当新文档加入知识库时自动触发，内化医家学术体系并生成概要文件。Invoke when user says '开始内化', '处理新文档', '录入新医家', or when new documents are detected in the knowledge base."
trigger: "检测到知识库中有新文档加入时，或用户说'开始内化'、'处理新文档'、'录入新医家'"
---

# 文档内化工具 Skill

## 功能概述

当新文档（PDF/TXT/Word）被添加到知识库时，本Skill自动触发，完成以下工作：
1. 读取并理解文档内容
2. 识别文档所属医家及其学术体系
3. 按照6维度结构提取医家学术信息
4. 生成医家概要文件
5. 更新总览索引
6. 更新shared_config.md配置（如需新增颜色配置）

## 触发条件

- 用户将新PDF/TXT/Word文件放入 `e:\叶天士\叶天士\00-原著全文\` 的任何子目录
- 用户明确要求"内化新文档"或"录入新医家"
- 用户说"开始内化"或"处理新文档"

## 文件路径

- Skill定义：`e:\叶天士\叶天士\skills\文档内化工具\SKILL.md`
- Agent Prompt：`e:\叶天士\叶天士\skills\文档内化工具\agent_prompt.md`
- 医家概要输出目录：`e:\叶天士\叶天士\00-原著全文\各家学说库\医家体系概要\`
- 总览索引：`e:\叶天士\叶天士\00-原著全文\各家学说库\医家体系概要\总览索引.md`
- 共享配置：`e:\叶天士\叶天士\skills\common\shared_config.md`
