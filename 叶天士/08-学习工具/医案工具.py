"""
中医温病医案处理工具 - 简化版
"""

import os
import json

def create_template():
    """创建医案模板"""
    template = """# 【填写医案标题】

## 医家
【填写医生姓名，如：吴鞠通、叶天士】

## 患者信息
- 性别: 【男/女】
- 年龄: 【年龄】
- 职业: 【职业】

## 症状
【在此处填写症状，用逗号或换行分隔】

## 舌脉
- 舌象: 【舌象描述】
- 脉象: 【脉象描述】

## 诊断
【辨证结果】

## 处方
【处方内容】

---
标签: 【标签，用逗号分隔】
"""
    return template

def main():
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "09-医案学习数据库")

    print("=" * 50)
    print("中医温病医案处理工具")
    print("=" * 50)
    print()
    print("1. 生成医案模板")
    print("2. 退出")
    print()

    choice = input("请选择 (1-2): ").strip()

    if choice == "1":
        raw_dir = os.path.join(base_dir, "医案库")
        os.makedirs(raw_dir, exist_ok=True)
        template = create_template()
        template_path = os.path.join(raw_dir, "00-医案模板.md")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template)
        print(f"[OK] 模板已生成: {template_path}")
        print()
        print("下一步:")
        print("1. 复制模板文件")
        print("2. 重命名为您的医案文件名")
        print("3. 填入医案内容")
        print("4. 开始学习！")
    else:
        print("再见！")

    input("\n按回车键退出...")

if __name__ == "__main__":
    main()
