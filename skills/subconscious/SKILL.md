---
name: subconscious
description: "跨会话长期记忆（潜意识）：零配置自动启用——会话开始自动注入历史背景（whisper），对话中自动记录关键事件/决策/困惑/偏好，收尾自动整理（联想/凝缩/遗忘/梦境）。不依赖用户唤醒、不依赖 harness 注册技能；启用条件=AI 能读仓库 CLAUDE.md + 能运行 Python（无 Python 时降级为纯文本读写）。"
---

# 潜意识记忆 Skill（Subconscious）

本 Skill 提供**跨会话长期记忆**：自动记录会话中的关键事件（决策、问题、反复出现的模式、学习偏好），在本地完成联想、凝缩、遗忘与"梦境"整理，并在下次会话开始时注入相关历史背景——让 AI 不再"每次从零开始"。

核心：**意识层（模型）主动记录 → 本地 Python 管道自动整理 → 下次会话 whisper 注入**。全部本地执行，零 LLM token 成本。

## 〇、零配置自动启用（本 Skill 的使用方式）

> **本 Skill 不需要用户触发、不需要 harness 注册**（不依赖 `.trae/skills/`、`.zcode/skills/` 等机制）。启用条件只有两条：① AI 能读仓库根 `CLAUDE.md`；② AI 能运行 Python（或降级为纯文本读写，见"五、无 Python 降级"）。
>
> **驱动机制**：仓库 `CLAUDE.md` 的"★ 潜意识学情记忆（subconscious·零配置自动启用）"章节规定了三个强制时机（会话开始跑 pre_session / 对话中记录 / 收尾跑 post_session）。本文件是执行细则——规则的细节（记什么、怎么记、格式、边界）以本文件为准。
>
> **AI 执行清单**（每次会话）：会话开始 → 运行 pre_session.py 取背景；对话中 → 按"二、对话中：记录规则"静默记录；会话收尾 → 运行 post_session.py。三个动作都不向用户提及。

## 一、会话开始（必做）

每次会话开始时，先运行（cwd 为仓库根目录）：

```bash
python .subconscious/hooks/pre_session.py
```

- 有输出 → 输出是历史联想（whisper），将其作为本次会话的背景提示。
- 无输出 → 无预注入包，正常开始。

## 二、对话中：记录规则

只记"值得记的"，宁少勿滥。**必须记录**：

| 场景 | 示例 | event_type |
|---|---|---|
| 做了关键决策/选择 | 决定用 PostgreSQL 替代 MySQL | `decision` |
| 解决了一个问题/Bug | 定位并修复了缓存穿透 | `problem` |
| 反复出现的行为模式 | 用户第三次踩同一个坑 | `pattern` |
| 学了新知识/洞察 | 第一次接触某概念并理解 | `insight` |
| 用户偏好/习惯 | 用户偏好先给例子再讲原理 | `pattern` |
| 学习/工作进度节点 | 某课程某章节学完 | `note` |

**不记录**：普通查询、简单问答、闲聊、常规操作。

记录命令（**中文/非 ASCII 文本只能走环境变量通道**——Windows PowerShell 5.1 下命令行内嵌中文会乱码；不要用 `python -c` 内嵌中文）：

```powershell
$env:EVENT_TEXT='用户学完伤寒论太阳病篇第12条桂枝汤证'; $env:EVENT_TAGS='伤寒论,太阳病,桂枝汤'; $env:EVENT_TYPE='insight'; python .subconscious/hooks/dsh_log.py
```

Linux/macOS 同样适用（环境变量通道跨平台无损）：

```bash
EVENT_TEXT='用户学完伤寒论太阳病篇第12条桂枝汤证' EVENT_TAGS='伤寒论,太阳病,桂枝汤' EVENT_TYPE='insight' python .subconscious/hooks/dsh_log.py
```

### 标签规范

- tags 用**标准词表**：领域/课程名 + 模块名 + 术语（如中医场景：课程名 + 六经术语 + 方证名）。
- 每条 2–5 个标签，**第一个标签必须是领域/课程名**。
- 用规范术语，不用口语变体（"怕冷"→"恶寒"）。匹配靠标签，词表越规范召回越准。

## 三、会话收尾（必做）

对话明显结束时，运行：

```powershell
python .subconscious/hooks/post_session.py
```

它会执行 5 阶段管道（编码→联想→凝缩→固化→预注入）+ 遗忘扫描 + 梦境处理，并输出统计。

## 四、手动命令

| 需要 | 执行 |
|---|---|
| 查看记忆状态 | `python .subconscious/hooks/dsh_cmd.py status` |
| 回忆相关记忆 | `$env:EVENT_TEXT='关键词'; python .subconscious/hooks/dsh_cmd.py recall` |
| 触发一次梦境整理 | `python .subconscious/hooks/dsh_cmd.py dream` |

## 五、数据与存储

- 记忆库：环境变量 `SUBCONSCIOUS_MEMORY_DIR` 指定，默认 `~/.dsh/subconscious-memory/`（纯 JSON，可备份，删除即清空记忆）
- 会话记忆（v2 主存储）：`<项目根>/.workbuddy/memory/sessions/session-memory.jsonl`（一行一 JSON，含 `scope`/`skill` 字段，追加式，**不自动清空**）
- 旧缓冲（v1 兼容）：`.subconscious/session_log.jsonl`（管道跑完并入持久记忆后归档，不再作为主存储）
- 环境变量：`SUBCONSCIOUS_MODE`（whisper/full/dream/off）、`SUBCONSCIOUS_FORGET_THRESHOLD`（遗忘阈值，默认 0.1）、`SUBCONSCIOUS_DECAY_RATE`（衰减率，默认 0.05）

## 五·五、无 Python 降级（AI 纯文本读写版）

> 环境无法运行 Python 时，本 Skill 退化为"AI 直接读写 JSON"——**只要 AI 能读写文件，记忆功能就可用**：

| 时机 | Python 版 | 降级版（AI 直接读写） |
|:---|:---|:---|
| 会话开始 | `python .subconscious/hooks/pre_session.py` | 读记忆库目录（`SUBCONSCIOUS_MEMORY_DIR` 或默认 `~/.dsh/subconscious-memory/`）下的 JSON 文件，提取相关历史作为背景 |
| 对话中 | `dsh_log.py`（环境变量通道） | 追加一行到 `session-memory.jsonl`：`{"ts":"...","session_id":"...","scope":"project","skill":"<本skill>","type":"insight","text":"事件内容","tags":["课程","术语"]}` |
| 会话收尾 | `post_session.py` | 读 session-memory.jsonl 中“本次新增”条目跑管道；只推进指针，不删除记忆文件 |

**降级纪律**：格式尽量与 Python 版一致（字段：ts/text/tags/type）；整理频率可降低（每次会话收尾做一次即可）；宁少勿滥——只记"值得记的"。

## 六、原则

- 潜意识**只读不写**用户文件（只写自己的记忆库）
- 不阻塞主流程：记录失败静默忽略
- whisper 每条 ≤80 字，≤3 条，话痨是潜意识的天敌
- 凝缩阈值：同类记忆 ≥3 条才压缩为 insight
- 遗忘：重要性衰减 5%，低于 0.1 归档（不删除）
- 记录行为**不要向用户提及**
- **记忆是缓存不是事实源**：课程进度/笔记以进度追踪文件（运行副本）为准；记忆与文件冲突时以文件为准，并更新记忆消除偏差；收到"继续学习"先读进度文件再参考记忆，禁止凭记忆断言用户无进度或重新评估（详见仓库 CLAUDE.md ★ 进度与个人数据事实源解析）

## 七、中医场景示例（本仓库默认语境）

- 用户明确表示跳过某内容（如"温病三宝临床无使用空间，不深入学习"）→ 记 `insight`，标签 `温病,温病三宝,临床用药`，此后**不要反复追问该内容**。
- 用户反复混淆两个证候 → 记 `pattern`（"第三次混淆少阴寒化与太阴寒湿"），下次会话主动提醒。
- 三焦/卫气营血内容打标签时同时打上对应的六经标签（如 `温病,卫分证,太阴`）。
