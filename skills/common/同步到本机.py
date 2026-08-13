# -*- coding: utf-8 -*-
"""
同步到本机.py v2 - 把主版本 skills 分发到 .zcode/skills 运行副本
设计: 副本 = 触发入口（SKILL.md + common），数据文件在 vault 主版本（唯一数据源）
  - 副本每技能只保留 SKILL.md（ZCode 触发用），并在必读声明后插入"本机运行说明"
    指向 vault 主版本的完整文件（课程流程.md/进度追踪.md/笔记）
  - common/ 与 _新建技能模板/ 全量复制（副本相对引用 ../common/ 自动成立）
  - 进度/笔记读写都在 vault 主版本，不存在双份数据
"""
import io
import os
import shutil
import sys

# 本机默认位置（正斜杠形式；发布版使用时可传入参数指定目标）
VAULT_SKILLS = sys.argv[2] if len(sys.argv) > 2 else r'E:/叶天士/叶天士/skills'
ZCODE_SKILLS = sys.argv[1] if len(sys.argv) > 1 else r'E:/叶天士/.zcode/skills'

RUN_NOTE = '''

> **【本机运行说明】本副本仅为触发入口。** 教学所需的全部数据文件（课程流程.md / 进度追踪.md / 笔记目录）位于 vault 主版本：
> `{vault}\\{skill}\\`（进度追踪.md）、`{vault}\\{note_dir}\\`（笔记）
> **开始教学前，读取 vault 主版本的 `课程流程.md` 与 `进度追踪.md`；笔记写入 vault 课程目录；所有读写都在主版本进行，勿在本副本读写数据。**

'''

NOTE_DIRS = {
    '经典临床': '01-经典临床（正课）',
    '黄帝内经': '03-黄帝内经（正课）',
    '经典基础': '05-经典基础',
    '诊疗基础': '06-诊疗基础',
}


def sync():
    if not os.path.isdir(VAULT_SKILLS):
        print('错误: 找不到主版本 %s' % VAULT_SKILLS)
        return 1
    if os.path.exists(ZCODE_SKILLS):
        shutil.rmtree(ZCODE_SKILLS)
    os.makedirs(ZCODE_SKILLS)
    count = 0
    for entry in os.listdir(VAULT_SKILLS):
        src = os.path.join(VAULT_SKILLS, entry)
        dst = os.path.join(ZCODE_SKILLS, entry)
        if os.path.isdir(src):
            if entry.startswith('_') or entry == 'common':
                # 模板/common 全量
                shutil.copytree(src, dst)
                print('✓ 目录 %s/' % entry)
                count += 1
            elif os.path.isfile(os.path.join(src, 'SKILL.md')):
                # 技能: 只复制 SKILL.md 并附加运行说明
                os.makedirs(dst, exist_ok=True)
                with io.open(os.path.join(src, 'SKILL.md'), encoding='utf-8') as f:
                    c = f.read()
                note_dir = NOTE_DIRS.get(entry, '')
                c = c + RUN_NOTE.format(skill=entry, note_dir=note_dir, vault=VAULT_SKILLS)
                with io.open(os.path.join(dst, 'SKILL.md'), 'w', encoding='utf-8') as f:
                    f.write(c)
                print('✓ 技能 %s/（触发入口）' % entry)
                count += 1
        elif os.path.isfile(src):
            shutil.copy2(src, dst)
            count += 1
    print('完成：同步 %d 项到 %s' % (count, ZCODE_SKILLS))
    print('数据文件（进度/笔记）唯一数据源: %s' % VAULT_SKILLS)
    return 0


if __name__ == '__main__':
    sys.exit(sync())
