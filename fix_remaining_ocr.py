#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""扫描并修复所有TXT文件中的残留OCR错误"""

import os

files = {
    '词典': r'e:\叶天士\叶天士\00-原著全文\黄帝内经类\黄帝内经词典.txt',
    '素问校释': r'e:\叶天士\叶天士\00-原著全文\黄帝内经类\黄帝内经素问校释.txt',
    '白话全译': r'e:\叶天士\叶天士\00-原著全文\黄帝内经类\黄帝内经附白话全译.txt',
    '胡希恕金匮': r'e:\叶天士\叶天士\00-原著全文\金匮要略类\胡希恕金匮要略讲座.txt',
}

# 错误→正确 映射表
fixes = {
    '索问': '素问',
    '灵要': '灵枢',
    '灵概': '灵枢',
    '灵槐': '灵枢',
    '素门': '素问',
    '束问': '素问',
    '金匿': '金匮',
    '伤蹄': '伤寒',
    '徐国祭': '徐国仟',
    '张灿理': '张灿玾',
}

total_fixed = 0

for name, path in files.items():
    if not os.path.exists(path):
        print(f'[{name}] 文件不存在: {path}')
        continue

    with open(path, 'r', encoding='utf-8-sig') as f:
        content = f.read()

    file_fixed = 0
    details = []

    for wrong, correct in fixes.items():
        count = content.count(wrong)
        if count > 0:
            content = content.replace(wrong, correct)
            file_fixed += count
            details.append(f'  {wrong} -> {correct}: {count}处')

    if file_fixed > 0:
        # 同时更新注释中的说明
        old_note = '仍有少量残留字符级错误（如索问应为素问），但词条释义和引证内容基本可读，可用于RAG检索。'
        new_note = '所有已知OCR字符错误均已修复，词条释义和引证内容可读，可用于RAG检索。'
        if old_note in content:
            content = content.replace(old_note, new_note)
            details.append('  注释已更新（移除残留错误说明）')

        with open(path, 'w', encoding='utf-8-sig') as f:
            f.write(content)
        print(f'[{name}] 修复 {file_fixed} 处:')
        for d in details:
            print(d)
        total_fixed += file_fixed
    else:
        print(f'[{name}] 无残留错误')

print(f'\n总计修复: {total_fixed} 处')
