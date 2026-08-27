# -*- coding: utf-8 -*-
# 迁移合并个人数据 v1.0 — 把旧文件夹里的个人数据合并进当前文件夹（零依赖）
# 用法: 迁移合并.bat "旧文件夹路径"  （或把旧文件夹拖到 迁移合并.bat 图标上）
# 合并内容: 与 个人数据备份.ps1 相同的个人数据清单
# 原则: 绝不删除、绝不覆盖当前文件夹中的任何个人文件。
#       若当前文件夹已存在同名个人文件，旧文件会以 "原名.旧版备份_时间戳" 保留，
#       两边数据都不丢。公共文件（skills/、00-原著全文/ 等）不做任何处理，
#       以新版本为准。

param([string]$OldRoot = "")

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

if (-not $OldRoot) {
    Write-Host "[ERROR] 未指定旧文件夹。用法: 迁移合并.bat \"\"旧文件夹路径\"\""
    exit 1
}
if (-not (Test-Path -LiteralPath $OldRoot)) {
    Write-Host "[ERROR] 找不到旧文件夹: $OldRoot"
    exit 1
}

# 定位当前仓库根: 本脚本位于 <仓库根>/工具/个人数据备份与迁移/
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$newRoot   = Split-Path -Parent (Split-Path -Parent $scriptDir)
$oldVault  = Join-Path $OldRoot '叶天士'
$oldApp    = Join-Path $OldRoot 'tcm-tutor-agent'
$newVault  = Join-Path $newRoot '叶天士'
$newApp    = Join-Path $newRoot 'tcm-tutor-agent'

$stamp = "{0:yyyyMMdd_HHmmss}" -f (Get-Date)
$added = 0
$conflict = 0

function Merge-One {
    param([string]$OldSrc, [string]$NewDst, [string]$Label)
    if (-not (Test-Path -LiteralPath $OldSrc)) {
        Write-Host ("  [--] 旧侧不存在，跳过: {0}" -f $Label)
        return
    }
    $parent = Split-Path -Parent $NewDst
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    if (-not (Test-Path -LiteralPath $NewDst)) {
        Copy-Item -LiteralPath $OldSrc -Destination $NewDst -Recurse -Force
        Write-Host ("  [OK] 新增: {0}" -f $Label)
        $script:added++
    }
    else {
        # 新侧已有同名个人文件: 不覆盖，旧侧另存为 原名.旧版备份_时间戳（原名+后缀，统一格式）
        $name = Split-Path -Leaf $NewDst
        $alt  = Join-Path $parent ("{0}.旧版备份_{1}" -f $name, $stamp)
        Copy-Item -LiteralPath $OldSrc -Destination $alt -Recurse -Force
        Write-Host ("  [!!] 冲突保留双方: {0}  ->  {1}" -f $Label, (Split-Path -Leaf $alt))
        $script:conflict++
    }
}

Write-Host "============================================================"
Write-Host " 迁移合并个人数据"
Write-Host "============================================================"
Write-Host "旧文件夹: $OldRoot"
Write-Host "当前文件夹: $newRoot"
Write-Host ""
Write-Host "-- 1. 课程笔记目录 (vault) --"
$noteDirs = @(
    '01-经典临床（正课）', '02-经典临床（复习）',
    '03-黄帝内经（正课）', '04-黄帝内经（复习）',
    '05-经典基础', '06-诊疗基础', '07-温病历史课（旧）'
)
foreach ($d in $noteDirs) {
    Merge-One (Join-Path $oldVault $d) (Join-Path $newVault $d) "叶天士/$d"
}
Write-Host "-- 2. 进度与入门文件 (vault) --"
Merge-One (Join-Path $oldVault '学习进度追踪.md') (Join-Path $newVault '学习进度追踪.md') '叶天士/学习进度追踪.md'
Merge-One (Join-Path $oldVault '快速入门.md')      (Join-Path $newVault '快速入门.md')      '叶天士/快速入门.md'
Write-Host "-- 3. 应用数据 (tcm-tutor-agent) --"
Merge-One (Join-Path $oldApp '.env')             (Join-Path $newApp '.env')             'tcm-tutor-agent/.env'
Merge-One (Join-Path $oldApp 'data\users.db')    (Join-Path $newApp 'data\users.db')    'tcm-tutor-agent/data/users.db'
Merge-One (Join-Path $oldApp 'data\config.json') (Join-Path $newApp 'data\config.json') 'tcm-tutor-agent/data/config.json'
Write-Host ""
Write-Host "完成: 新增 $added 项, 冲突保留双方 $conflict 项（旧文件以 .旧版备份_时间戳 命名，双方都在）。"
Write-Host ""
Write-Host "注意:"
Write-Host "  1. 公共文件（skills/ 00-原著全文/ 等）未做任何处理 —— 以新版本为准，这是预期行为。"
Write-Host "  2. 若 users.db 出现冲突（新旧两套账号），旧库在 tcm-tutor-agent/data/ 下以"
Write-Host "     users.db.旧版备份_时间戳 保留；如需找回旧账号数据，请手动替换并重启应用。"
Write-Host "  3. 请保留旧文件夹一段时间，确认新文件夹一切正常后再删除。"
