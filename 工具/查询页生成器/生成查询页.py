# -*- coding: utf-8 -*-
"""
生成查询页 v1.0 — 从知识库生成单文件《中医经典知识查询.html》

用法:
    python 生成查询页.py [输出文件路径]
    （不传参数时输出到仓库根目录: 中医经典知识查询.html）

数据源（相对本脚本，符合仓库"相对路径"宪法）:
    ../../叶天士/00-原著全文/   —— 9 个子库的 .txt / .md（排除 历史版本/ 与 README.md）
    ../../根目录衍生资料        —— 教学大纲/脉象/金匮条文分类等
    ../../金匮方证六经归属表.html —— 方证速查表（提取 style + 表格，iframe 内嵌）

输出特性:
    - 单文件 HTML，双击即用、可离线、可分享
    - 分类导航 + 全文检索 + 方证速查 + 分节锚点跳转 + 医案检索
    - 纯原文陈列，不做任何解读

依赖: 仅 Python 3.8+ 标准库，零第三方依赖。
"""
import os
import sys
import re
import json
import html
import datetime

try:  # Windows 控制台中文输出
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))          # 工具/查询页生成器 -> 仓库根
KB_DIR = os.path.join(REPO_ROOT, '叶天士', '00-原著全文')
CHART_HTML = os.path.join(REPO_ROOT, '金匮方证六经归属表.html')

# 仓库根目录的衍生资料（有学术价值，作为独立分类）
DERIVED_FILES = [
    '伤寒杂病论统一教学大纲.md',
    '金匮条文分类结果.txt',
    '金匮非方药条文六经归属.txt',
    '脉象三层指感_27脉.md',
    '脉象大全_伤寒来苏集十脉与濒湖脉学二十七脉.md',
]

EXCLUDE_DIRS = {'历史版本'}
EXCLUDE_NAMES = {'README.md'}

# 分节标题识别规则（用于目录跳转）
ANCHOR_PATTERNS = [
    re.compile(r'^【[^】]{1,40}】'),                                        # 【篇名】
    re.compile(r'^第[一二三四五六七八九十百千0-9]+[条卷篇章课]'),            # 第X条/卷/篇/章
    re.compile(r'^[\u4e00-\u9fff·（）()]{2,24}(篇|卷)第[一二三四五六七八九十百千0-9]+'),  # XX篇第X
]


def decode_bytes(data):
    """编码探测：utf-8-sig -> utf-8 -> gb18030"""
    for enc in ('utf-8-sig', 'utf-8', 'gb18030'):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode('utf-8', errors='replace')


def scan_kb(kb_dir):
    """扫描知识库，返回 [{cat, rel, path, size}]（排除历史版本与 README）"""
    items = []
    for root, dirs, files in os.walk(kb_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fn in files:
            if fn in EXCLUDE_NAMES:
                continue
            ext = os.path.splitext(fn)[1].lower()
            if ext not in ('.txt', '.md'):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, kb_dir)
            items.append({
                'cat': rel.split(os.sep)[0],
                'rel': rel.replace(os.sep, '/'),
                'path': full,
                'size': os.path.getsize(full),
            })
    items.sort(key=lambda x: (x['cat'], x['rel']))
    return items


def make_anchors(text):
    """返回 (anchors, offsets)。
    anchors: 分节标题 [{t:标题, i:行号, o:字符偏移}]
    offsets: 每行起始字符偏移（用于搜索命中定位行号）"""
    anchors = []
    offsets = []
    pos = 0
    for i, line in enumerate(text.split('\n')):
        offsets.append(pos)
        s = line.strip()
        if s and any(p.match(s) for p in ANCHOR_PATTERNS):
            anchors.append({'t': s[:40], 'i': i, 'o': pos})
        pos += len(line) + 1
    return anchors, offsets


def build_chart_doc(repo_root):
    """提取速查表 <style>（去 @import）与 container 起至 </html> 的片段，
    组装为 iframe srcdoc 用的独立文档，样式零冲突。"""
    with open(os.path.join(repo_root, '金匮方证六经归属表.html'),
              'r', encoding='utf-8', errors='replace') as f:
        src = f.read()
    m = re.search(r'<style>(.*?)</style>', src, re.S)
    style = m.group(1) if m else ''
    style = re.sub(r'@import[^;]+;', '', style)  # 去掉联网字体，保证离线可用
    start = src.index('<div class="container">')
    end = src.index('</html>')
    body = src[start:end]
    return ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            '<style>' + style + '</style></head><body>' + body + '</body></html>')


def fmt_size(n):
    if n >= 1048576:
        return '%.1fMB' % (n / 1048576)
    if n >= 1024:
        return '%.0fKB' % (n / 1024)
    return '%dB' % n


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>中医经典知识查询</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body { height: 100%; }
  body {
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    background: #f5f0eb; color: #2c2c2c; line-height: 1.75; font-size: 15px;
    display: flex; flex-direction: column; overflow: hidden;
  }
  /* ===== 顶栏 ===== */
  .q-header {
    background: linear-gradient(135deg, #2c1810 0%, #4a3428 50%, #2c1810 100%);
    color: #f5f0eb; padding: 18px 28px 14px; flex: none;
  }
  .q-header h1 { font-family: "Noto Serif SC", "SimSun", serif; font-size: 22px; font-weight: 700; }
  .q-header .q-sub { font-size: 12px; opacity: 0.75; margin-top: 2px; }
  .q-stats { display: flex; gap: 22px; margin-top: 10px; flex-wrap: wrap; }
  .q-stat { text-align: center; }
  .q-stat .n { font-size: 20px; font-weight: 700; color: #d4a574; }
  .q-stat .l { font-size: 11px; opacity: 0.7; }
  /* ===== 工具条 ===== */
  .q-toolbar {
    display: flex; gap: 10px; align-items: center; padding: 10px 20px;
    background: #fff; border-bottom: 1px solid #e0d5cc; flex: none; flex-wrap: wrap;
  }
  .q-search { flex: 1; min-width: 220px; }
  .q-search input {
    width: 100%; padding: 8px 14px; font-size: 15px; border: 1px solid #d8cbbd;
    border-radius: 20px; outline: none; background: #faf7f3;
  }
  .q-search input:focus { border-color: #b98d5f; background: #fff; }
  .q-scope { padding: 7px 10px; font-size: 14px; border: 1px solid #d8cbbd; border-radius: 8px; background: #fff; }
  .q-chart-btn {
    padding: 7px 16px; font-size: 14px; border: none; border-radius: 8px; cursor: pointer;
    background: linear-gradient(135deg, #b98d5f, #8c6239); color: #fff; font-weight: 600;
  }
  .q-chart-btn:hover { filter: brightness(1.08); }
  .q-toolbar-hint { font-size: 12px; color: #999; }
  /* ===== 主布局 ===== */
  .q-main-wrap { display: flex; flex: 1; min-height: 0; }
  .q-aside {
    width: 270px; flex: none; overflow-y: auto; background: #fbf8f4;
    border-right: 1px solid #e0d5cc; padding: 10px 8px;
  }
  .q-aside details { margin-bottom: 4px; }
  .q-aside summary {
    cursor: pointer; font-weight: 700; font-size: 14px; color: #4a3428;
    padding: 7px 10px; border-radius: 6px; background: #f2ece4; list-style: none;
  }
  .q-aside summary:hover { background: #eae1d5; }
  .q-aside summary::before { content: '▸ '; color: #b98d5f; }
  .q-aside details[open] summary::before { content: '▾ '; }
  .q-aside details[open] summary { background: #eae1d5; }
  .q-file {
    display: flex; justify-content: space-between; align-items: baseline; gap: 8px;
    padding: 4px 10px 4px 22px; font-size: 13px; cursor: pointer; border-radius: 4px; color: #3a3a3a;
  }
  .q-file:hover { background: #efe7dc; color: #2c1810; }
  .q-file.active { background: #d4a574; color: #fff; }
  .q-file .sz { font-size: 11px; color: #b0a08e; }
  .q-file.active .sz { color: #f5e9dc; }
  /* ===== 主区 ===== */
  .q-main { flex: 1; overflow-y: auto; padding: 0; min-width: 0; }
  .q-welcome { padding: 40px 50px; max-width: 860px; margin: 0 auto; }
  .q-welcome h2 { font-family: "Noto Serif SC", "SimSun", serif; color: #4a3428; margin-bottom: 12px; }
  .q-welcome p { margin-bottom: 10px; color: #555; }
  .q-welcome .q-card {
    background: #fff; border: 1px solid #e0d5cc; border-radius: 10px; padding: 16px 20px; margin-top: 14px;
  }
  .q-welcome .q-card h3 { font-size: 15px; color: #4a3428; margin-bottom: 8px; }
  .q-catlink {
    display: inline-block; margin: 4px 6px 4px 0; padding: 5px 14px; font-size: 13px;
    background: #f2ece4; border: 1px solid #e0d5cc; border-radius: 20px; cursor: pointer; color: #4a3428;
  }
  .q-catlink:hover { background: #d4a574; color: #fff; border-color: #d4a574; }
  /* 文件视图 */
  .q-filehead {
    background: #fff; border-bottom: 1px solid #e0d5cc; padding: 14px 24px;
    position: sticky; top: 0; z-index: 5; display: flex; justify-content: space-between; align-items: baseline;
  }
  .q-fname { font-family: "Noto Serif SC", "SimSun", serif; font-size: 19px; font-weight: 700; color: #2c1810; }
  .q-fmeta { font-size: 12px; color: #999; }
  .q-toc {
    background: #fbf8f4; border-bottom: 1px solid #e0d5cc; padding: 8px 24px;
    display: flex; flex-wrap: wrap; gap: 6px; max-height: 96px; overflow-y: auto; position: sticky; top: 52px; z-index: 4;
  }
  .q-toc a {
    font-size: 12px; color: #6b5340; background: #f2ece4; padding: 2px 10px;
    border-radius: 12px; cursor: pointer; text-decoration: none; white-space: nowrap;
  }
  .q-toc a:hover { background: #d4a574; color: #fff; }
  .q-body {
    font-family: "Noto Serif SC", "Source Han Serif SC", "SimSun", serif;
    font-size: 15px; line-height: 1.75; color: #2c2c2c; padding: 20px 28px 60px;
    white-space: pre-wrap; word-break: break-all; background: #fffdf9;
  }
  .q-body .q-hl { background: #ffd76e; border-radius: 2px; }
  /* 搜索面板 */
  .q-results { padding: 16px 24px; }
  .q-results .q-rtitle { font-size: 14px; color: #4a3428; font-weight: 700; margin-bottom: 10px; }
  .q-res-item {
    display: flex; justify-content: space-between; gap: 12px; padding: 8px 12px; margin-bottom: 6px;
    background: #fff; border: 1px solid #e8ded2; border-radius: 8px; cursor: pointer; font-size: 13px;
  }
  .q-res-item:hover { border-color: #b98d5f; background: #fdf9f4; }
  .q-res-item .c { color: #b98d5f; font-weight: 700; white-space: nowrap; }
  .q-res-item .s { color: #888; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .q-none { color: #999; padding: 16px 24px; font-size: 14px; }
  /* 速查 iframe */
  .q-chart { width: 100%; border: none; display: block; }
  /* 滚动条 */
  ::-webkit-scrollbar { width: 9px; height: 9px; }
  ::-webkit-scrollbar-thumb { background: #d8cbbd; border-radius: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
</style>
</head>
<body>

<div class="q-header">
  <h1>中医经典知识查询</h1>
  <div class="q-sub">伤寒论 · 金匮要略 · 温病条辨 · 黄帝内经 · 医案 · 本草 · 诊法 · 病源 · 各家学说 —— 纯原文陈列，离线可用</div>
  <div class="q-stats" id="qStats"></div>
</div>

<div class="q-toolbar">
  <div class="q-search"><input id="qInput" type="text" placeholder="全文检索：输入方剂、条文、症状、医家关键词…"></div>
  <select id="qScope" class="q-scope" title="检索范围"></select>
  <button class="q-chart-btn" id="qChartBtn">金匮方证六经归属表</button>
  <span class="q-toolbar-hint" id="qHint"></span>
</div>

<div class="q-main-wrap">
  <aside class="q-aside" id="qAside"></aside>
  <main class="q-main" id="qMain"></main>
</div>

<script>
"use strict";
/* 数据（由生成器注入；'</' 已转义为 '<\/'） */
const DATA = __DATA_JSON__;

const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const fmtKB = n => n >= 1048576 ? (n / 1048576).toFixed(1) + 'MB' : n >= 1024 ? Math.round(n / 1024) + 'KB' : n + 'B';

/* ---------- 统计与分类树 ---------- */
function buildStats() {
  const totalFiles = DATA.cats.reduce((a, c) => a + c.files.length, 0) + DATA.derived.length;
  const chars = DATA.stats ? DATA.stats.chars : 0;
  const html = [
    ['<span class="n">' + DATA.cats.length + '</span><span class="l">知识库分类</span>'],
    ['<span class="n">' + totalFiles + '</span><span class="l">文本文件</span>'],
    ['<span class="n">' + (chars / 10000).toFixed(1) + '万</span><span class="l">总字数</span>'],
    ['<span class="n">' + esc(DATA.generated) + '</span><span class="l">生成时间</span>'],
  ].map(p => '<div class="q-stat">' + p.join('') + '</div>').join('');
  $('qStats').innerHTML = html;
}

function fileId(f) { return f.id; }

function buildTree() {
  let h = '';
  DATA.cats.forEach(cat => {
    h += '<details open><summary>' + esc(cat.name) + ' (' + cat.files.length + ')</summary>';
    cat.files.forEach(f => {
      h += '<div class="q-file" data-id="' + esc(f.id) + '" data-name="' + esc(f.name) + '" data-cat="' + esc(cat.name) + '">' +
           '<span class="t">' + esc(f.name) + '</span><span class="sz">' + fmtKB(f.size) + '</span></div>';
    });
    h += '</details>';
  });
  h += '<details><summary>衍生资料 (' + DATA.derived.length + ')</summary>';
  DATA.derived.forEach(f => {
    h += '<div class="q-file" data-id="' + esc(f.id) + '" data-name="' + esc(f.name) + '" data-cat="衍生资料">' +
         '<span class="t">' + esc(f.name) + '</span><span class="sz">' + fmtKB(f.size) + '</span></div>';
  });
  h += '</details>';
  $('qAside').innerHTML = h;
  $('qAside').querySelectorAll('.q-file').forEach(el => {
    el.onclick = () => openFile(el.dataset.id, el.dataset.name, el.dataset.cat);
  });
}

/* ---------- 渲染文件 ---------- */
function bisect(arr, v) {
  let lo = 0, hi = arr.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (arr[mid] <= v) lo = mid + 1; else hi = mid; }
  return lo;
}

function openFile(id, name, cat, hitOffset) {
  setActive(id);
  const text = DATA.texts[id];
  const anchors = DATA.anchors[id] || [];
  const offsets = DATA.offsets[id] || [0];
  const lines = text.split('\n');
  let h = '<div class="q-filehead"><span class="q-fname">' + esc(name) + '</span>' +
          '<span class="q-fmeta">' + esc(cat || '') + ' · ' + lines.length + ' 行 · ' + fmtKB(text.length) + '</span></div>';
  if (anchors.length) {
    h += '<div class="q-toc">' + anchors.map((a, k) => '<a data-k="' + k + '">' + esc(a.t) + '</a>').join('') + '</div>';
  }
  h += '<pre class="q-body">';
  const parts = new Array(lines.length);
  for (let i = 0; i < lines.length; i++) parts[i] = '<span class="q-ln" id="qL' + i + '">' + esc(lines[i]) + '</span>';
  h += parts.join('\n') + '\n</pre>';
  $('qMain').innerHTML = h;
  $('qMain').querySelectorAll('.q-toc a').forEach(a => {
    a.onclick = () => document.getElementById('qL' + anchors[+a.dataset.k].i).scrollIntoView({ block: 'start' });
  });
  if (hitOffset != null && hitOffset >= 0) {
    const ln = Math.max(0, bisect(offsets, hitOffset) - 1);
    const el = document.getElementById('qL' + ln);
    if (el) {
      el.classList.add('q-hl');
      setTimeout(() => el.scrollIntoView({ block: 'start' }), 30);
    }
  }
  $('qInput').value = '';
  $('qHint').textContent = '';
}

function setActive(id) {
  $('qAside').querySelectorAll('.q-file').forEach(el => el.classList.toggle('active', el.dataset.id === id));
}

/* ---------- 全文检索 ---------- */
let searchTimer = null;
$('qInput').addEventListener('input', () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(runSearch, 250);
});
$('qScope').addEventListener('change', () => { const q = $('qInput').value.trim(); if (q) runSearch(); });

function scopeIds() {
  const sc = $('qScope').value;
  if (sc === 'all') return Object.keys(DATA.texts);
  if (sc === 'derived') return DATA.derived.map(d => d.id);
  return Object.keys(DATA.texts).filter(k => k.indexOf(sc + '/') === 0);
}

function runSearch() {
  const q = $('qInput').value.trim();
  if (!q) { $('qMain').innerHTML = welcomeHTML(); return; }
  const ids = scopeIds();
  const results = [];
  for (let i = 0; i < ids.length; i++) {
    const id = ids[i], t = DATA.texts[id];
    const first = t.indexOf(q);
    if (first === -1) continue;
    let n = 1, p = first + q.length;
    while (n < 300) { p = t.indexOf(q, p); if (p === -1) break; n++; p += q.length; }
    results.push({ id, n, first });
  }
  results.sort((a, b) => b.n - a.n);
  renderResults(results, q);
}

function renderResults(results, q) {
  const names = {};
  DATA.cats.forEach(c => c.files.forEach(f => names[f.id] = f.name));
  DATA.derived.forEach(f => names[f.id] = f.name);
  let h = '<div class="q-results"><div class="q-rtitle">「' + esc(q) + '」共 ' + results.length + ' 个文件命中（点击打开并定位）</div>';
  if (!results.length) { h = '<div class="q-none">没有找到包含「' + esc(q) + '」的内容。可尝试换关键词，或缩小检索范围。</div>'; }
  results.slice(0, 200).forEach(r => {
    const t = DATA.texts[r.id];
    const s = t.slice(Math.max(0, r.first - 25), r.first + q.length + 40).replace(/\s+/g, ' ');
    h += '<div class="q-res-item" data-id="' + esc(r.id) + '" data-first="' + r.first + '">' +
         '<span class="t">' + esc(names[r.id] || r.id) + '</span>' +
         '<span class="c">' + r.n + ' 处</span><span class="s">…' + esc(s) + '…</span></div>';
  });
  h += '</div>';
  $('qMain').innerHTML = h;
  $('qMain').querySelectorAll('.q-res-item').forEach(el => {
    el.onclick = () => openFile(el.dataset.id, names[el.dataset.id] || el.dataset.id, '', +el.dataset.first);
  });
}

/* ---------- 方证速查 ---------- */
$('qChartBtn').onclick = () => {
  setActive('');
  $('qMain').innerHTML = '<iframe class="q-chart" id="qChart" srcdoc="' + DATA.chartEsc + '"></iframe>';
  const f = $('qChart');
  f.onload = () => { f.style.height = (f.contentWindow.document.documentElement.scrollHeight + 40) + 'px'; };
  $('qInput').value = ''; $('qHint').textContent = '';
};

/* ---------- 欢迎页 ---------- */
function welcomeHTML() {
  let h = '<div class="q-welcome"><h2>中医经典知识查询</h2>';
  h += '<p>本页收录《伤寒论》《金匮要略》《温病条辨》《黄帝内经》等经典原文、医家讲稿、医案、本草、诊法、病源与各家学说文本，' +
       '以及教学大纲、方证六经归属表、脉象等衍生资料，<b>纯原文陈列、不做解读</b>，离线可用。</p>';
  h += '<div class="q-card"><h3>使用方式</h3><p>① 左侧分类树点击文件直接阅读；② 顶部搜索框全文检索（可选范围：全部 / 医案类 / 各家学说库等），点击结果自动定位；' +
       '③ 「金匮方证六经归属表」按钮打开方证速查表；④ 正文顶部出现分节目录时点击可跳转（如伤寒论按【篇】、金匮按篇章）。</p></div>';
  h += '<div class="q-card"><h3>分类快捷入口</h3>';
  DATA.cats.forEach(c => { h += '<span class="q-catlink" data-cat="' + esc(c.name) + '">' + esc(c.name) + '</span>'; });
  h += '<span class="q-catlink" data-cat="衍生资料">衍生资料</span>';
  h += '</div></div>';
  return h;
}

$('qMain').innerHTML = welcomeHTML();
$('qMain').querySelectorAll('.q-catlink').forEach(el => {
  el.onclick = () => {
    const cat = el.dataset.cat;
    $('qAside').querySelectorAll('details').forEach(d => { if (d.querySelector('summary').textContent.indexOf(cat) === 0) d.open = true; });
    $('qAside').scrollIntoView({ block: 'start' });
  };
});

/* ---------- 初始化 ---------- */
(function init() {
  buildStats();
  buildTree();
  const sc = $('qScope');
  let opts = '<option value="all">检索范围：全部</option>';
  DATA.cats.forEach(c => { opts += '<option value="' + esc(c.name) + '">' + esc(c.name) + '</option>'; });
  opts += '<option value="derived">衍生资料</option>';
  sc.innerHTML = opts;
})();
</script>
</body>
</html>
"""


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO_ROOT, '中医经典知识查询.html')

    print('=' * 60)
    print(' 中医经典知识查询页生成器 v1.0')
    print('=' * 60)
    print('知识库目录: %s' % KB_DIR)

    if not os.path.isdir(KB_DIR):
        print('[ERROR] 找不到知识库目录: %s' % KB_DIR)
        return 1

    # 1. 扫描知识库
    items = scan_kb(KB_DIR)
    print('扫描到 %d 个文本文件（9 个子库）' % len(items))

    cats = []
    by_cat = {}
    for it in items:
        by_cat.setdefault(it['cat'], []).append(it)
    for cat in sorted(by_cat):
        files = []
        for it in by_cat[cat]:
            name = os.path.splitext(it['rel'].rsplit('/', 1)[-1])[0]
            files.append({'id': it['rel'], 'name': name, 'size': it['size']})
        cats.append({'name': cat, 'files': files})
        print('  [%s] %d 文件' % (cat, len(files)))

    # 2. 衍生资料
    derived = []
    for fn in DERIVED_FILES:
        p = os.path.join(REPO_ROOT, fn)
        if os.path.isfile(p):
            derived.append({'id': 'derived/' + fn, 'name': fn, 'size': os.path.getsize(p), 'path': p})
        else:
            print('  [警告] 衍生资料缺失: %s' % fn)
    print('衍生资料: %d 个文件' % len(derived))

    # 3. 读取全部文本 + 生成锚点/行偏移索引
    print('读取全文并建立分节索引 ...')
    texts, anchors_map, offsets_map = {}, {}, {}
    total_chars = 0
    for it in items:
        with open(it['path'], 'rb') as f:
            text = decode_bytes(f.read())
        texts[it['rel']] = text
        total_chars += len(text)
        anchors_map[it['rel']], offsets_map[it['rel']] = make_anchors(text)
    for d in derived:
        with open(d['path'], 'rb') as f:
            text = decode_bytes(f.read())
        texts[d['id']] = text
        total_chars += len(text)
        anchors_map[d['id']], offsets_map[d['id']] = make_anchors(text)
    print('总字数: %d（%.1fMB UTF-8）' % (total_chars, total_chars / 1048576))

    # 4. 速查表
    print('提取方证速查表 ...')
    chart_doc = build_chart_doc(REPO_ROOT)
    chart_esc = html.escape(chart_doc, quote=True)
    print('速查表文档: %d 字符' % len(chart_doc))

    # 5. 组装数据
    data = {
        'generated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
        'cats': cats,
        'derived': [{'id': d['id'], 'name': d['name'], 'size': d['size']} for d in derived],
        'texts': texts,
        'anchors': anchors_map,
        'offsets': offsets_map,
        'stats': {'files': len(items) + len(derived), 'chars': total_chars},
        'chartEsc': chart_esc,
    }
    print('序列化 JSON ...')
    payload = json.dumps(data, ensure_ascii=False)
    payload = payload.replace('</', '<\\/')  # 防止 </script> 截断
    print('JSON 体积: %.1fMB' % (len(payload.encode('utf-8')) / 1048576))

    # 6. 写出
    print('组装 HTML 并写出 ...')
    page = HTML_TEMPLATE.replace('__DATA_JSON__', payload)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(page)
    print('完成: %s（%.1fMB）' % (out, os.path.getsize(out) / 1048576))
    return 0


if __name__ == '__main__':
    sys.exit(main())
