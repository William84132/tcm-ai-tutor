---
name: subconscious
description: "跨会话长期记忆（潜意识）：自动记录关键事件/决策/困惑/偏好，本地联想、凝缩、遗忘与梦境整理，新会话开始自动注入相关历史背景。Invoke when the user asks about memory status ('潜意识状态','回忆一下'), or check memory at session start."
---

# 潜意识记忆 Skill（Subconscious）

本 Skill 提供**跨会话长期记忆**：自动记录会话中的关键事件（决策、问题、反复出现的模式、学习偏好），在本地完成联想、凝缩、遗忘与"梦境"整理，并在下次会话开始时注入相关历史背景——让 AI 不再"每次从零开始"。

核心：**意识层（模型）主动记录 → 本地 Python 管道自动整理 → 下次会话 whisper 注入**。全部本地执行，零 LLM token 成本。

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
- 会话日志缓冲：`.subconscious/session_log.jsonl`（管道跑完自动清空）
- 环境变量：`SUBCONSCIOUS_MODE`（whisper/full/dream/off）、`SUBCONSCIOUS_FORGET_THRESHOLD`（遗忘阈值，默认 0.1）、`SUBCONSCIOUS_DECAY_RATE`（衰减率，默认 0.05）

## 六、原则

- 潜意识**只读不写**用户文件（只写自己的记忆库）
- 不阻塞主流程：记录失败静默忽略
- whisper 每条 ≤80 字，≤3 条，话痨是潜意识的天敌
- 凝缩阈值：同类记忆 ≥3 条才压缩为 insight
- 遗忘：重要性衰减 5%，低于 0.1 归档（不删除）
- 记录行为**不要向用户提及**

## 七、中医场景示例（本仓库默认语境）

- 用户明确表示跳过某内容（如"温病三宝临床无使用空间，不深入学习"）→ 记 `insight`，标签 `温病,温病三宝,临床用药`，此后**不要反复追问该内容**。
- 用户反复混淆两个证候 → 记 `pattern`（"第三次混淆少阴寒化与太阴寒湿"），下次会话主动提醒。
- 三焦/卫气营血内容打标签时同时打上对应的六经标签（如 `温病,卫分证,太阴`）。
