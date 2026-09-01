# -*- coding: utf-8 -*-
# 迁移合并个人数据 v2.0 — 把旧文件夹里的个人数据合并进当前文件夹（零依赖）
# 用法: 迁移合并.bat "旧文件夹路径"  （或把旧文件夹拖到 迁移合并.bat 图标上）
#
# v2.0 改动（2026-09-01）：
#   会话记忆从"全局潜意识目录"改为"项目级 + 全局级两套 session-memory.jsonl"，
#   合并时按 (ts, text) 去重，不删、不覆盖、不丢数据。
#
# 合并内容: 与 backup_data.ps1 v2 相同的个人数据清单（目录冲突时逐文件合并）
# 原则: 绝不删除、绝不覆盖当前文件夹中的任何个人文件。

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
    $isDir = (Get-Item -LiteralPath $OldSrc).PSIsContainer
    if (-not (Test-Path -LiteralPath $NewDst)) {
        $parent = Split-Path -Parent $NewDst
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
        Copy-Item -LiteralPath $OldSrc -Destination $NewDst -Recurse -Force
        Write-Host ("  [OK] 新增: {0}" -f $Label)
        $script:added++
    }
    elseif (-not $isDir) {
        $parent = Split-Path -Parent $NewDst
        $name = Split-Path -Leaf $NewDst
        $alt  = Join-Path $parent ("{0}.旧版备份_{1}" -f $name, $stamp)
        Copy-Item -LiteralPath $OldSrc -Destination $alt -Recurse -Force
        Write-Host ("  [!!] 冲突保留双方: {0}  ->  {1}" -f $Label, (Split-Path -Leaf $alt))
        $script:conflict++
    }
    else {
        Merge-Dir $OldSrc $NewDst $Label
    }
}

function Merge-Dir {
    param([string]$OldDir, [string]$NewDir, [string]$Label)
    New-Item -ItemType Directory -Path $NewDir -Force | Out-Null
    $items = Get-ChildItem -LiteralPath $OldDir -Force
    foreach ($it in $items) {
        $newItem = Join-Path $NewDir $it.Name
        if ($it.PSIsContainer) {
            Merge-Dir $it.FullName $newItem ($Label + '/' + $it.Name)
        }
        elseif (Test-Path -LiteralPath $newItem) {
            $alt = Join-Path $NewDir ("{0}.旧版备份_{1}" -f $it.Name, $stamp)
            Copy-Item -LiteralPath $it.FullName -Destination $alt -Force
            Write-Host ("  [!!] 冲突保留双方: {0}/{1}  ->  {2}" -f $Label, $it.Name, (Split-Path -Leaf $alt))
            $script:conflict++
        }
        else {
            Copy-Item -LiteralPath $it.FullName -Destination $newItem -Force
            Write-Host ("  [OK] 新增: {0}/{1}" -f $Label, $it.Name)
            $script:added++
        }
    }
}

function Merge-Memory {
    param([string]$OldFile, [string]$NewFile, [string]$Label)
    if (-not (Test-Path -LiteralPath $OldFile)) {
        Write-Host ("  [--] 旧侧不存在，跳过: {0}" -f $Label); return
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $NewFile) -Force | Out-Null
    $seen = @{}
    if (Test-Path -LiteralPath $NewFile) {
        foreach ($line in (Get-Content -LiteralPath $NewFile -Encoding UTF8)) {
            if ($line.Trim() -eq '') { continue }
            try { $e = $line | ConvertFrom-Json; $k = ($e.ts) + '|' + ($e.text) } catch { $k = $line }
            $seen[$k] = 1
        }
    }
    $total = 0; $added = 0
    foreach ($line in (Get-Content -LiteralPath $OldFile -Encoding UTF8)) {
        if ($line.Trim() -eq '') { continue }
        $total++
        try { $e = $line | ConvertFrom-Json; $k = ($e.ts) + '|' + ($e.text) } catch { $k = $line }
        if ($seen.ContainsKey($k)) { continue }
        Add-Content -LiteralPath $NewFile -Value $line -Encoding UTF8
        $added++; $seen[$k] = 1
    }
    Write-Host ("  [OK] {0}: 旧侧 {1} 条，新增 {2} 条（去重合并，不删不覆盖）" -f $Label, $total, $added)
}

Write-Host "============================================================"
Write-Host " 迁移合并个人数据 v2.0"
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

Write-Host "-- 4. 会话记忆 (v2 · 去重合并) --"
$newProjMem = Join-Path $newRoot '.workbuddy\memory\sessions\session-memory.jsonl'
$newGlobMem = Join-Path $HOME '.workbuddy\memory\sessions\session-memory.jsonl'
Merge-Memory (Join-Path $OldRoot '记忆\项目_session-memory.jsonl') $newProjMem '项目记忆'
Merge-Memory (Join-Path $OldRoot '记忆\全局_session-memory.jsonl') $newGlobMem '全局记忆'
Merge-Memory (Join-Path $OldRoot '记忆\旧位置_session_log.jsonl')  $newProjMem '旧位置会话缓冲'

Write-Host ""
Write-Host "完成: 新增 $added 项, 冲突保留双方 $conflict 项（旧文件以 .旧版备份_时间戳 命名，双方都在）。"
Write-Host ""
Write-Host "注意:"
Write-Host "  1. 公共文件（skills/ 00-原著全文/ 等）未做任何处理 —— 以新版本为准，这是预期行为。"
Write-Host "  2. 若 users.db 出现冲突（新旧两套账号），旧库在 tcm-tutor-agent/data/ 下以"
Write-Host "     users.db.旧版备份_时间戳 保留；如需找回旧账号数据，请手动替换并重启应用。"
Write-Host "  3. 会话记忆已按 (ts,text) 去重合并到 <项目根>\.workbuddy\memory\sessions\session-memory.jsonl，重复不丢、缺的补齐。"
Write-Host "  4. 请保留旧文件夹一段时间，确认新文件夹一切正常后再删除。"
