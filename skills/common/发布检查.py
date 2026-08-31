# -*- coding: utf-8 -*-
"""
发布检查.py - 发布版内容核对工具
用法:
  python 发布检查.py            # 检查当前 skills/ 目录（默认源）
  python 发布检查.py <目录>     # 检查指定目录（如发布版副本）
功能: 扫描个人内容/密钥/本机绝对路径，输出发布核对报告
  - 个人内容: 笔记/ 目录、进度追踪.md 含学习记录、个人 json、.env/config.json
  - 密钥: sk- 前缀、API_KEY 等
  - 本机路径: 盘符反斜杠形式的绝对路径（如 盘符:\\目录）、file:/// 协议形式
"""
import io
import os
import re
import sys

PERSONAL_DIRS = ['笔记', '已学习', '历史版本', '历史脚本', '历史课']
PERSONAL_FILES = ['个人用户档案', '.env', 'config.json', '_sync_test',
                  # 潜意识记忆运行数据（个人学情，禁止入库）：.jsonl 覆盖 session_log.jsonl 等
                  'whisper_package', '.jsonl']
SECRET_PATTERNS = [
    re.compile(r'sk-[A-Za-z0-9]{10,}', re.I),
    re.compile(r'(api[_-]?key|secret|token)\s*[:=]\s*(?!["\']?helloworld|["\']?your_|["\']?example|["\']?xxx|["\']?change_me|sys\.argv)\S{8,}', re.I),
]
ABSOLUTE_PATTERNS = [
    re.compile(r'(?<![\\])[A-Za-z]:\\(?![a-z])', re.I),  # 盘符反斜杠形式（排除换行/制表转义）
    re.compile(r'file:///[A-Za-z]:', re.I),              # file:/// 协议盘符形式
]
PROGRESS_LEARNED_MARKERS = ['已完成课次', '学习记录列表', '间隔复习追踪表']
SKIP_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf', '.exe', '.rar', '.zip', '.epub', '.db', '.pkl'}


def check_dir(root):
    issues = []
    for dirpath, dirnames, filenames in os.walk(root):
        # 跳过 .git / __pycache__（二进制与缓存）
        dirnames[:] = [d for d in dirnames if d not in ('.git', '__pycache__')]
        # 目录级个人内容
        for d in dirnames:
            if d in PERSONAL_DIRS:
                issues.append(('个人目录', os.path.join(dirpath, d)))
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            ext = os.path.splitext(fn)[1].lower()
            # 个人文件
            for p in PERSONAL_FILES:
                if p in fn:
                    issues.append(('个人文件', rel))
            # 进度追踪：判断是否为初始模板（数据行出现 已复习/新学/条文学习 即个人）
            if fn == '进度追踪.md':
                with io.open(full, encoding='utf-8', errors='ignore') as f:
                    c = f.read()
                if re.search(r'\|\s*(已复习|新学|条文学习)\s*\|', c) or ('学习记录列表' in c and '尚无记录' not in c):
                    issues.append(('进度含学习记录(非初始模板)', rel))
            # 文本内容检查（含 .py：脚本中可能存在本机路径/密钥，2026-08-17 修复原跳过盲区）
            if ext in SKIP_EXTS:
                continue
            try:
                with io.open(full, encoding='utf-8', errors='ignore') as f:
                    c = f.read()
            except Exception:
                continue
            for pat in SECRET_PATTERNS:
                m = pat.search(c)
                if m:
                    issues.append(('疑似密钥: %s...' % m.group(0)[:20], rel))
                    break
            for pat in ABSOLUTE_PATTERNS:
                m = pat.search(c)
                if m:
                    issues.append(('本机绝对路径: %s' % m.group(0), rel))
                    break
    return issues


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root = os.path.abspath(root)
    print('发布检查: %s' % root)
    print('=' * 60)
    issues = check_dir(root)
    if not issues:
        print('✓ 通过：未发现个人内容/密钥/本机绝对路径，可发布')
        return 0
    print('⚠ 发现 %d 项问题：' % len(issues))
    for kind, rel in issues:
        print('  [%s] %s' % (kind, rel))
    return 1


if __name__ == '__main__':
    sys.exit(main())
