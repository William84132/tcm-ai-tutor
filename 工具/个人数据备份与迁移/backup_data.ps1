# -*- coding: utf-8 -*-
# 个人数据备份 v2.0 — 一键备份个人学习数据（零依赖，Windows PowerShell 5.1+）
# 用法: 个人数据备份.bat [目标文件夹]  （不传参数则备份到本目录下 备份_时间戳/）
#
# v2.0 改动（2026-09-01 修复"备份成功但记忆是空的"）：
#   - 会话记忆改为扫两套路径：项目级 .workbuddy/memory/sessions/ + 全局 ~/.workbuddy/memory/sessions/
#     （v1 只扫 ~/.dsh/subconscious-memory，该目录在多数环境根本不存在，导致记忆备份为空白）
#   - 兼容旧位置 .subconscious/session_log.jsonl 与 已迁移_session_log_*.jsonl
#   - 新增：仓库根层 AI 生成笔记（排除与发布版同名的公共文件）
#   - 关键项缺失由静默"跳过"改为 [WARN]
#   - 结束前自检：记忆条数为 0 直接 [ERROR] 并给出排查提示
#
# 备份内容（个人数据边界，详见 使用说明.md）:
#   vault 课程笔记目录: 01-经典临床（正课）/ 02-经典临床（复习）/ 03-黄帝内经（正课）/
#                       04-黄帝内经（复习）/ 05-经典基础/ 06-诊疗基础/ 07-温病历史课（旧）/
#   vault 进度文件:     学习进度追踪.md / 快速入门.md
#   应用数据:          tcm-tutor-agent\.env / data\users.db / data\config.json
#   会话记忆（v2）:     <项目根>\.workbuddy\memory\sessions\session-memory.jsonl  （项目级）
#                     ~\.workbuddy\memory\sessions\session-memory.jsonl        （全局级）
#   旧位置兼容:        .subconscious\session_log.jsonl / 已迁移_session_log_*.jsonl
#   根层生成笔记:      仓库根 *.md / *.txt（排除与 GitHub上传内容\ 同名的公共文件）
# 原则: 只复制、绝不删除任何源文件。

param([string]$Target = "")

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 定位仓库根: 本脚本位于 <仓库根>/工具/个人数据备份与迁移/
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot  = Split-Path -Parent (Split-Path -Parent $scriptDir)
$vault     = Join-Path $repoRoot '叶天士'
$app       = Join-Path $repoRoot 'tcm-tutor-agent'
$publicRoot = Join-Path $repoRoot 'GitHub上传内容'

# 备份目标
if (-not $Target) {
    $Target = Join-Path $scriptDir ("备份_{0:yyyyMMdd_HHmmss}" -f (Get-Date))
}
$Target = [System.IO.Path]::GetFullPath($Target)
New-Item -ItemType Directory -Path $Target -Force | Out-Null

$copied = 0
$skipped = 0
$warned = 0

function Copy-One {
    param([string]$Src, [string]$Rel, [switch]$Required)
    if (Test-Path -LiteralPath $Src) {
        $dst = Join-Path $Target $Rel
        New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force | Out-Null
        Copy-Item -LiteralPath $Src -Destination $dst -Recurse -Force
        Write-Host ("  [OK] {0}" -f $Rel)
        $script:copied++
    }
    elseif ($Required) {
        Write-Host ("  [WARN] 关键项缺失: {0}" -f $Rel) -ForegroundColor Yellow
        Write-Host ("         预期位置: {0}" -f $Src) -ForegroundColor DarkYellow
        $script:warned++
    }
    else {
        Write-Host ("  [--] 不存在，跳过: {0}" -f $Rel)
        $script:skipped++
    }
}

Write-Host "============================================================"
Write-Host " 个人数据备份 v2.0"
Write-Host "============================================================"
Write-Host "仓库根目录: $repoRoot"
Write-Host "备份目标  : $Target"
Write-Host ""
Write-Host "-- 1. 课程笔记目录 (vault) --"
#   注：温病历史课在运行副本中归档为 _archive-07-温病历史课（旧），两个名字都列入，
#       存在哪个备份哪个（v1 只列 07-温病历史课（旧），导致该目录从未被备份）。
$noteDirs = @(
    '01-经典临床（正课）', '02-经典临床（复习）',
    '03-黄帝内经（正课）', '04-黄帝内经（复习）',
    '05-经典基础', '06-诊疗基础', '07-温病历史课（旧）',
    '_archive-07-温病历史课（旧）'
)
foreach ($d in $noteDirs) {
    Copy-One (Join-Path $vault $d) (Join-Path '叶天士' $d)
}
Write-Host "-- 2. 进度与入门文件 (vault) --"
Copy-One (Join-Path $vault '学习进度追踪.md') '叶天士/学习进度追踪.md'
Copy-One (Join-Path $vault '快速入门.md')      '叶天士/快速入门.md'
Write-Host "-- 3. 应用数据 (tcm-tutor-agent) --"
Copy-One (Join-Path $app '.env')                'tcm-tutor-agent/.env'
Copy-One (Join-Path $app 'data\users.db')       'tcm-tutor-agent/data/users.db'
Copy-One (Join-Path $app 'data\config.json')    'tcm-tutor-agent/data/config.json'

Write-Host "-- 4. 会话记忆 (v2 · 项目级 + 全局级) --"
$projMemDir = Join-Path $repoRoot '.workbuddy\memory\sessions'
$globMemDir = Join-Path $HOME '.workbuddy\memory\sessions'
Copy-One (Join-Path $projMemDir 'session-memory.jsonl') '记忆/项目_session-memory.jsonl' -Required
Copy-One (Join-Path $globMemDir 'session-memory.jsonl') '记忆/全局_session-memory.jsonl'
# 技能归属副本（skills/<技能>/memory/）
$skillsDirs = @(Join-Path $repoRoot '叶天士\skills')
foreach ($sd in $skillsDirs) {
    if (Test-Path -LiteralPath $sd) {
        Get-ChildItem -LiteralPath $sd -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object {
            $sm = Join-Path $_.FullName 'memory\session-memory.jsonl'
            if (Test-Path -LiteralPath $sm) {
                Copy-One $sm ('记忆/技能副本/{0}_session-memory.jsonl' -f $_.Name)
            }
        }
    }
}

Write-Host "-- 5. 旧位置兼容 (.subconscious) --"
$legacy = Join-Path $repoRoot '.subconscious'
Copy-One (Join-Path $legacy 'session_log.jsonl') '记忆/旧位置_session_log.jsonl'
Get-ChildItem -LiteralPath $legacy -Filter '已迁移_session_log_*.jsonl' -File -ErrorAction SilentlyContinue |
    ForEach-Object { Copy-One $_.FullName ('记忆/旧位置_{0}' -f $_.Name) }

Write-Host "-- 6. 仓库根层生成笔记 (排除公共文件) --"
$rootNotes = Get-ChildItem -LiteralPath $repoRoot -File -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Extension -in @('.md', '.txt') }
foreach ($f in $rootNotes) {
    $isPublic = Test-Path -LiteralPath (Join-Path $publicRoot $f.Name)
    if ($isPublic) {
        Write-Host ("  [--] 公共文件，跳过: {0}" -f $f.Name)
        $script:skipped++
    }
    else {
        Copy-One $f.FullName (Join-Path '根层笔记' $f.Name)
    }
}

# ---------------------------------------------------------------- 自检
Write-Host ""
Write-Host "-- 7. 备份自检 --"
$memCount = 0
$memFiles = @(
    (Join-Path $Target '记忆/项目_session-memory.jsonl'),
    (Join-Path $Target '记忆/旧位置_session_log.jsonl')
)
foreach ($mf in $memFiles) {
    if (Test-Path -LiteralPath $mf) {
        # 显式 UTF8：中文 Windows 默认按 GBK 读取会乱码，行数统计虽不受影响，
        # 但保持与 merge_data.ps1 一致，避免后续扩展时踩同一个坑。
        $n = (Get-Content -LiteralPath $mf -Encoding UTF8 -ErrorAction SilentlyContinue |
              Where-Object { $_.Trim() -ne '' } | Measure-Object).Count
        $memCount += $n
        Write-Host ("  {0}: {1} 条" -f (Split-Path -Leaf $mf), $n)
    }
}
if ($memCount -eq 0) {
    Write-Host "  [ERROR] 备份出的会话记忆为 0 条 —— 备份不完整！" -ForegroundColor Red
    Write-Host "          排查顺序：" -ForegroundColor Red
    Write-Host "          1) 检查 <项目根>\.workbuddy\memory\sessions\session-memory.jsonl 是否有内容" -ForegroundColor Red
    Write-Host "          2) 若无，运行 session_logger.py 的 migrate_legacy() 迁移旧缓冲" -ForegroundColor Red
    Write-Host "          3) 确认本项目确实产生过会话记忆（否则 0 条属正常）" -ForegroundColor Red
}
else {
    Write-Host ("  [OK] 会话记忆合计 {0} 条" -f $memCount) -ForegroundColor Green
}

Write-Host ""
Write-Host "完成: 复制 $copied 项, 跳过 $skipped 项, 关键项告警 $warned 项。"
Write-Host "备份位置: $Target"
Write-Host ""
Write-Host "提示: 更新系统前先运行本脚本；换新系统时把整个备份文件夹"
Write-Host "复制过去，再在新系统运行 [迁移合并.bat] 即可（或手动对照还原）。"
