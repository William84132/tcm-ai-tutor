# -*- coding: utf-8 -*-
"""
中医学习系统 - 统一入口/系统概览
显示四课程学习进度和系统状态
"""
import os
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 动态：skills/common 上两级 = vault 根
SKILLS_DIR = os.path.join(BASE_DIR, "skills")
TEXT_DIR = os.path.join(BASE_DIR, "00-原著全文")

COURSES = [
    {"name": "经典临床", "key": "jingdianlinchuang", "skill_dir": "经典临床",
     "progress_file": os.path.join(BASE_DIR, "skills", "经典临床", "进度追踪.md"),
     "trigger_learn": "开始经典临床学习 / 继续经典临床学习",
     "trigger_test": "开始测试",
     "color": "紫色", "question_steps": "四步提问法"},
    {"name": "伤寒论", "key": "shanghan", "skill_dir": "伤寒论",
     "progress_file": os.path.join(SKILLS_DIR, "伤寒论", "进度追踪.md"),
     "trigger_learn": "开始伤寒学习 / 继续伤寒学习",
     "trigger_test": "开始伤寒测试",
     "color": "棕色", "question_steps": "四步提问法"},
    {"name": "金匮要略", "key": "jingui", "skill_dir": "金匮要略",
     "progress_file": os.path.join(SKILLS_DIR, "金匮要略", "进度追踪.md"),
     "trigger_learn": "开始金匮学习 / 继续金匮学习",
     "trigger_test": "开始金匮测试",
     "color": "绿色", "question_steps": "四步提问法"},
    {"name": "黄帝内经", "key": "huangdi", "skill_dir": "黄帝内经",
     "progress_file": os.path.join(SKILLS_DIR, "黄帝内经", "进度追踪.md"),
     "trigger_learn": "开始内经学习 / 继续内经学习",
     "trigger_test": "—（无测试）",
     "color": "金色", "question_steps": "五步提问法（含哲学思辨）"},
]


def parse_progress_file(path):
    """解析进度文件，提取关键信息"""
    if not os.path.exists(path):
        return {"exists": False, "completed": 0, "level": "未开始", "last_date": "—"}
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    result = {"exists": True, "completed": 0, "level": "待评估", "last_date": "—"}
    
    # 提取已完成课次
    match = re.search(r'已完成课程次数\s*\|\s*(\d+)', content)
    if match:
        result["completed"] = int(match.group(1))
    else:
        # 尝试其他格式
        match = re.search(r'总课次\s*\|\s*(\d+)', content)
        if match:
            result["completed"] = int(match.group(1))
    
    # 提取层级
    match = re.search(r'当前层级\s*\|\s*(.+?)(?:\n|\|)', content)
    if match:
        result["level"] = match.group(1).strip()
    
    # 提取最后学习日期
    match = re.search(r'最后学习日期\s*\|\s*(.+?)(?:\n|\|)', content)
    if match:
        result["last_date"] = match.group(1).strip()
    
    return result


def get_text_stats():
    """获取原文库统计"""
    stats = {}
    
    # 伤寒论
    sh_path = os.path.join(TEXT_DIR, "伤寒论类", "伤寒论_完整版.txt")
    stats["伤寒论"] = os.path.getsize(sh_path) // 1024 if os.path.exists(sh_path) else 0
    
    # 金匮要略
    jg_path = os.path.join(TEXT_DIR, "金匮要略类", "金匮要略_完整版.txt")
    stats["金匮要略"] = os.path.getsize(jg_path) // 1024 if os.path.exists(jg_path) else 0
    
    # 医案
    case_dir = os.path.join(TEXT_DIR, "医案类")
    case_files = [f for f in os.listdir(case_dir) if f.endswith('.txt')] if os.path.exists(case_dir) else []
    stats["医案数量"] = len(case_files)
    
    return stats


def show_overview():
    """显示系统概览"""
    print("=" * 72)
    print("  中医学习系统 - 系统概览")
    print(f"  时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 72)
    
    print("\n【课程进度概览】\n")
    print(f"{'课程':<8} {'触发词（学习）':<22} {'触发词（测试）':<14} {'进度':<8} {'层级':<8} {'最后学习':<10}")
    print("-" * 72)
    
    for course in COURSES:
        prog = parse_progress_file(course["progress_file"])
        status = f"{prog['completed']}课" if prog['exists'] else "未开始"
        print(f"{course['name']:<8} {course['trigger_learn']:<22} {course['trigger_test']:<14} {status:<8} {prog['level']:<8} {prog['last_date']:<10}")
    
    print("\n【原文库状态】\n")
    stats = get_text_stats()
    print(f"  伤寒论完整版：{stats.get('伤寒论', 0)} KB")
    print(f"  金匮要略完整版：{stats.get('金匮要略', 0)} KB")
    print(f"  医案文件数量：{stats.get('医案数量', 0)} 个")
    
    print("\n【快速开始】\n")
    print("  说出以下任一触发词即可开始学习：")
    for course in COURSES:
        print(f"    - {course['name']}：{course['trigger_learn']}")
    print("\n  测试评估（黄帝内经无测试）：")
    for course in COURSES:
        if course['trigger_test'] != "—（无测试）":
            print(f"    - {course['name']}：{course['trigger_test']}")
    
    print("\n【课程特点】\n")
    for course in COURSES:
        print(f"  {course['name']}（{course['color']}）：{course['question_steps']}")
    
    print("\n" + "=" * 72)
    print("  提示：各课程进度独立记录，切换课程不影响其他课程")
    print("=" * 72)


def show_course_detail(course_name):
    """显示单个课程详情"""
    course = next((c for c in COURSES if c["name"] == course_name), None)
    if not course:
        print(f"未找到课程：{course_name}")
        return
    
    prog = parse_progress_file(course["progress_file"])
    
    print(f"\n【{course['name']}】")
    print(f"  学习触发词：{course['trigger_learn']}")
    print(f"  测试触发词：{course['trigger_test']}")
    print(f"  提问法：{course['question_steps']}")
    print(f"  当前层级：{prog['level']}")
    print(f"  已完成课次：{prog['completed']}")
    print(f"  最后学习日期：{prog['last_date']}")
    print(f"  进度文件：{course['progress_file']}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        # 显示指定课程详情
        show_course_detail(sys.argv[1])
    else:
        # 显示系统概览
        show_overview()
