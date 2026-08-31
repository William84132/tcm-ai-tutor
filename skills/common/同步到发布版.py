# -*- coding: utf-8 -*-
"""
同步到发布版.py — 把运行副本 skills 同步到 GitHub 发布模板
============================================================
方向：叶天士/skills（运行副本·权威源）  →  GitHub上传内容/skills（发布模板·无个人内容）

与「同步到本机.py」的区别：
  同步到本机.py  → Vault 主版本 → .zcode/skills（本机 harness 触发副本，只放 SKILL.md 入口）
  本脚本        → Vault 主版本 → GitHub上传内容/skills（完整发布模板，含数据文件）

核心规则（防止个人内容外泄）：
  1. 排除 进度追踪.md —— 发布版保留空模板（用户在本地填自己的进度）
  2. 排除 __pycache__ / .pyc / session_log.jsonl / 记忆库运行数据
  3. 目标编码统一 UTF-8 with BOM + LF（GitHub 与 Windows 记事本双友好）
  4. 内容归一化比对（去 BOM + CRLF→LF）后 hash 相同则跳过，避免无意义的文件改动

用法：
  python 同步到发布版.py                 # 默认路径
  python 同步到发布版.py --dry-run        # 只看会改什么，不写盘
  python 同步到发布版.py <源> <目标>       # 自定义路径
"""
import hashlib
import io
import os
import shutil
import sys

DEFAULT_SRC = r'E:/叶天士/叶天士/skills'
DEFAULT_DST = r'E:/叶天士/GitHub上传内容/skills'

# 永不发布的文件（含个人数据 / 编译产物 / 运行态数据）
EXCLUDE_FILES = {
    '进度追踪.md',        # 个人学习进度，发布版用空模板
    'session_log.jsonl',  # 潜意识运行日志
}
EXCLUDE_EXTS = {'.pyc', '.pyo'}
EXCLUDE_DIRS = {'__pycache__', '.obsidian', '.git'}


def norm_hash(path):
    """归一化后的内容指纹：去 BOM、CRLF→LF。用于判断"是否真的改了内容"。"""
    raw = open(path, 'rb').read()
    if raw[:3] == b'\xef\xbb\xbf':
        raw = raw[3:]
    text = raw.decode('utf-8', errors='ignore')
    return hashlib.md5(text.replace('\r\n', '\n').encode('utf-8')).hexdigest()


def write_publish(dst, text):
    """按发布规范写盘：UTF-8 with BOM + LF。"""
    text = text.replace('\r\n', '\n')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, 'wb') as f:
        f.write(b'\xef\xbb\xbf')
        f.write(text.encode('utf-8'))


def sync(src, dst, dry_run=False):
    if not os.path.isdir(src):
        print('错误：找不到运行副本 %s' % src)
        return 1

    synced, skipped, excluded = [], [], []

    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        rel_dir = os.path.relpath(dirpath, src)
        for fn in filenames:
            if fn in EXCLUDE_FILES or os.path.splitext(fn)[1] in EXCLUDE_EXTS:
                excluded.append(os.path.join(rel_dir, fn) if rel_dir != '.' else fn)
                continue
            s = os.path.join(dirpath, fn)
            rel = os.path.relpath(s, src)
            d = os.path.join(dst, rel)

            text = io.open(s, encoding='utf-8-sig', errors='ignore').read()
            new_hash = hashlib.md5(text.replace('\r\n', '\n').encode('utf-8')).hexdigest()

            if os.path.exists(d) and norm_hash(d) == new_hash:
                # 内容一致 —— 但如果目标编码不规范（无 BOM 或 CRLF），仍重写一次
                raw = open(d, 'rb').read()
                if raw[:3] == b'\xef\xbb\xbf' and b'\r\n' not in raw:
                    skipped.append(rel)
                    continue

            if dry_run:
                synced.append(rel)
                continue

            write_publish(d, text)
            synced.append(rel)

    print('=' * 60)
    print('运行副本 → 发布模板')
    print('  源: %s' % src)
    print('  目标: %s' % dst)
    print('=' * 60)
    print('\n【%s】%d 个文件' % ('将同步' if dry_run else '已同步', len(synced)))
    for r in sorted(synced):
        print('  + %s' % r)
    if skipped:
        print('\n【跳过·内容一致】%d 个' % len(skipped))
        for r in sorted(skipped)[:10]:
            print('  = %s' % r)
        if len(skipped) > 10:
            print('  ... 其余 %d 个' % (len(skipped) - 10))
    print('\n【排除·含个人数据或编译产物】%d 个' % len(excluded))
    for r in sorted(excluded):
        print('  - %s' % r)
    print('\n提示：进度追踪.md 发布版为空模板，本地进度绝不上行。')
    return 0


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    s = args[0] if len(args) > 0 else DEFAULT_SRC
    d = args[1] if len(args) > 1 else DEFAULT_DST
    sys.exit(sync(s, d, dry))
