# -*- coding: utf-8 -*-
# 个人数据备份 v1.0 — 一键备份个人学习数据（零依赖，Windows PowerShell 5.1+）
# 用法: 个人数据备份.bat [目标文件夹]  （不传参数则备份到本目录下 备份_时间戳/）
# 备份内容（个人数据边界，详见 使用说明.md）:
#   vault 课程笔记目录: 01-经典临床（正课）/ 02-经典临床（复习）/ 03-黄帝内经（正课）/
#                       04-黄帝内经（复习）/ 05-经典基础/ 06-诊疗基础/ 07-温病历史课（旧）/
#   vault 进度文件:     学习进度追踪.md / 快速入门.md
#   应用数据:          tcm-tutor-agent\.env / data\users.db / data\config.json
#   潜意识记忆库:      ~/.dsh/subconscious-memory/ （或 SUBCONSCIOUS_MEMORY_DIR 指定）
# 原则: 只复制、绝不删除任何源文件。

param([string]$Target = "")

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 定位仓库根: 本脚本位于 <仓库根>/工具/个人数据备份与迁移/
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot  = Split-Path -Parent (Split-Path -Parent $scriptDir)
$vault     = Join-Path $repoRoot '叶天士'
$app       = Join-Path $repoRoot 'tcm-tutor-agent'

# 备份目标
if (-not $Target) {
    $Target = Join-Path $scriptDir ("备份_{0:yyyyMMdd_HHmmss}" -f (Get-Date))
}
$Target = [System.IO.Path]::GetFullPath($Target)
New-Item -ItemType Directory -Path $Target -Force | Out-Null

$copied = 0
$skipped = 0

function Copy-One {
    param([string]$Src, [string]$Rel)
    if (Test-Path -LiteralPath $Src) {
        $dst = Join-Path $Target $Rel
        New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force | Out-Null
        Copy-Item -LiteralPath $Src -Destination $dst -Recurse -Force
        Write-Host ("  [OK] {0}" -f $Rel)
        $script:copied++
    }
    else {
        Write-Host ("  [--] 不存在，跳过: {0}" -f $Rel)
        $script:skipped++
    }
}

Write-Host "============================================================"
Write-Host " 个人数据备份"
Write-Host "============================================================"
Write-Host "仓库根目录: $repoRoot"
Write-Host "备份目标  : $Target"
Write-Host ""
Write-Host "-- 1. 课程笔记目录 (vault) --"
$noteDirs = @(
    '01-经典临床（正课）', '02-经典临床（复习）',
    '03-黄帝内经（正课）', '04-黄帝内经（复习）',
    '05-经典基础', '06-诊疗基础', '07-温病历史课（旧）'
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
Write-Host "-- 4. 潜意识记忆库 (subconscious) --"
$memDir = $env:SUBCONSCIOUS_MEMORY_DIR
if (-not $memDir) { $memDir = Join-Path $HOME '.dsh/subconscious-memory' }
Copy-One $memDir '个人数据/潜意识记忆库'
Write-Host ""
Write-Host "完成: 复制 $copied 项, 跳过 $skipped 项。"
Write-Host "备份位置: $Target"
Write-Host ""
Write-Host "提示: 更新系统前先运行本脚本；换新系统时把整个备份文件夹"
Write-Host "复制过去，再在新系统运行 [迁移合并.bat] 即可（或手动对照还原）。"
