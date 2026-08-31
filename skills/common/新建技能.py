# -*- coding: utf-8 -*-
"""
新建技能.py - 生成新技能目录骨架
用法: python 新建技能.py <技能名>
示例: python 新建技能.py 针灸入门
效果: 复制 _新建技能模板 到 skills/<技能名>/，并替换占位符
"""
import io
import os
import shutil
import sys

BASE = os.path.dirname(os.path.abspath(__file__))  # common/
SKILLS = os.path.dirname(BASE)  # skills/
TEMPLATE = os.path.join(SKILLS, '_新建技能模板')

PLACEHOLDERS = ['[技能名]', '[你的课程目录]']


def main():
    if len(sys.argv) < 2:
        print('用法: python 新建技能.py <技能名>')
        sys.exit(1)
    name = sys.argv[1].strip()
    target = os.path.join(SKILLS, name)
    if not os.path.isdir(TEMPLATE):
        print('错误: 找不到模板目录 %s' % TEMPLATE)
        sys.exit(1)
    if os.path.exists(target):
        print('错误: 技能目录已存在 %s' % target)
        sys.exit(1)
    shutil.copytree(TEMPLATE, target)
    # 替换占位符
    for root, _, files in os.walk(target):
        for fn in files:
            if not fn.endswith('.md'):
                continue
            path = os.path.join(root, fn)
            with io.open(path, encoding='utf-8') as f:
                content = f.read()
            changed = False
            for ph in PLACEHOLDERS:
                if ph in content:
                    content = content.replace(ph, name)
                    changed = True
            if changed:
                with io.open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
    print('✓ 技能骨架已生成: skills/%s/' % name)
    print('下一步：打开 %s/SKILL.md 填写触发词，并按 建技能说明.md 完成配置' % name)


if __name__ == '__main__':
    main()
