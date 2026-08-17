# 潜意识记忆 Skill（subconscious）

> 跨会话长期记忆补充组件：让 AI 记住"学习者/用户的学情"——进度、决策、困惑、反复混淆点、偏好——并在每次新会话开始时自动注入相关背景，不再每次从零开始。

本组件基于 [Square-Q/subconscious-skill](https://github.com/Square-Q/subconscious-skill)（MIT）适配：**面向中文场景修复了 Windows 命令行中文乱码问题（环境变量通道）**、改为逐事件独立编码（每条记录 = 一条记忆）、存储路径可配置。纯 Python 标准库，零外部依赖，零 LLM token 成本。

## 目录

```
skills/subconscious/SKILL.md   # 给 AI 的指令（接入后自动生效）
.subconscious/                 # Python 运行时（联想/凝缩/遗忘/梦境，全部本地执行）
```

## 安装（三选一）

**方式 A：手动模式（推荐，任何 AI 工具可用）**

1. 把 `skills/subconscious/` 和 `.subconscious/` 放入你的项目/vault 根目录（与 `skills/` 同级）。
2. AI 读取 `skills/subconscious/SKILL.md` 后按指令运行即可（SKILL.md 内命令均以仓库根为 cwd）。

**方式 B：DSH（DeepSeek Harness）**

把 `.subconscious/` 放入工作区根目录，`SKILL.md` 放入 `<工作区>/.dsh/skills/subconscious/SKILL.md`，重启 dsh web 后自动加载（skill catalog 出现 `subconscious` 即成功）。

**方式 C：Claude Code 自动 hooks（可选增强）**

在项目的 `.claude/settings.json` 中追加（实现会话开始/结束全自动触发，无需模型自觉执行）：

```json
{
  "hooks": {
    "SessionStart": [{ "matcher": "", "hooks": [{ "type": "command", "command": "python .subconscious/hooks/pre_session.py" }] }],
    "SessionEnd": [{ "matcher": "", "hooks": [{ "type": "command", "command": "python .subconscious/hooks/post_session.py" }] }]
  }
}
```

> Windows 用户注意：`.claude/settings.json` 中的 command 请使用 `python .subconscious/hooks/pre_session.py` 形式（上游的 `bash *.sh` 形式需要 Git Bash）。

## 使用

- 会话开始：`python .subconscious/hooks/pre_session.py`（读取历史联想 whisper）
- 对话中：按 SKILL.md 规则用 `dsh_log.py` 记录关键事件（**中文走环境变量通道**，见 SKILL.md）
- 会话结束：`python .subconscious/hooks/post_session.py`（5 阶段管道 + 遗忘扫描 + 梦境）
- 手动：`dsh_cmd.py status|recall|dream`

## 数据

- 记忆库：`SUBCONSCIOUS_MEMORY_DIR` 环境变量指定，默认 `~/.dsh/subconscious-memory/`（纯 JSON，可备份；删除即清空记忆）
- 会话日志缓冲：`.subconscious/session_log.jsonl`（管道跑完自动清空）

## 与主系统关系

本组件只记录**学习者维度**（进度/困惑/偏好），不替代课程知识库与教学规则——它是主系统的"长期记忆补充"，不是课程本身。中医场景默认示例见 SKILL.md 第七章。

## 许可

MIT。上游：[Square-Q/subconscious-skill](https://github.com/Square-Q/subconscious-skill)（Copyright (c) 2026 Subconscious Skill），本组件为其适配与增强版（Copyright (c) 2026 TCM AI Tutor）。
