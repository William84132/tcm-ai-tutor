"""
中医温病医案处理工具
"""

import os
import re
import json
from datetime import datetime

class MedicalCase:
    """医案数据结构"""
    def __init__(self):
        self.id = None
        self.title = ""
        self.doctor = ""
        self.patient_info = {}
        self.symptoms = []
        self.tongue_pulse = {}
        self.diagnosis = ""
        self.prescription = []
        self.notes = ""
        self.source = ""
        self.tags = []
        self.created_date = datetime.now().isoformat()

class MedicalCaseProcessor:
    """医案处理器"""

    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, "医案库")
        self.processed_dir = os.path.join(base_dir, "已学习")
        self.knowledge_dir = os.path.join(base_dir, "知识卡片")

        # 创建目录
        for d in [self.raw_dir, self.processed_dir, self.knowledge_dir]:
            os.makedirs(d, exist_ok=True)

    def parse_markdown(self, filepath):
        """解析markdown格式的医案"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        case = MedicalCase()
        case.id = os.path.splitext(os.path.basename(filepath))[0]
        case.source = filepath

        # 提取标题
        title_match = re.search(r'^#\s*(.+)$', content, re.MULTILINE)
        if title_match:
            case.title = title_match.group(1).strip()

        # 提取医家
        doctor_match = re.search(r'(?:医家|医生|医师)[:：]\s*(.+)$', content, re.MULTILINE)
        if doctor_match:
            case.doctor = doctor_match.group(1).strip()

        # 提取患者信息
        patient_sections = re.findall(r'(?:###?\s*)?(?:患者|性别|年龄|职业)[：:].*?(?=\n#{1,3}|$)', content, re.DOTALL)
        for section in patient_sections:
            if '性别' in section:
                match = re.search(r'性别[:：]\s*(\w+)', section)
                if match:
                    case.patient_info['gender'] = match.group(1).strip()
            if '年龄' in section:
                match = re.search(r'年龄[:：]\s*(\d+)', section)
                if match:
                    case.patient_info['age'] = int(match.group(1))
            if '职业' in section:
                match = re.search(r'职业[:：]\s*(.+)', section)
                if match:
                    case.patient_info['occupation'] = match.group(1).strip()

        # 提取症状
        symptom_match = re.search(r'(?:###?\s*)?(?:症状|主诉|现病史)[:：]?\s*(.*?)(?=\n#{1,3}|\n###?|\Z)', content, re.DOTALL)
        if symptom_match:
            symptom_text = symptom_match.group(1).strip()
            case.symptoms = [s.strip() for s in re.split(r'[，。；;、\n]', symptom_text) if s.strip()]

        # 提取舌脉
        tongue_match = re.search(r'(?:舌象|舌)[:：]\s*(.+?)(?=\n|$)', content)
        if tongue_match:
            case.tongue_pulse['tongue'] = tongue_match.group(1).strip()

        pulse_match = re.search(r'(?:脉象|脉)[:：]\s*(.+?)(?=\n|$)', content)
        if pulse_match:
            case.tongue_pulse['pulse'] = pulse_match.group(1).strip()

        # 提取诊断
        diag_match = re.search(r'(?:###?\s*)?(?:诊断|辨证)[:：]?\s*(.*?)(?=\n#{1,3}|\Z)', content, re.DOTALL)
        if diag_match:
            case.diagnosis = diag_match.group(1).strip()

        # 提取处方
        prescription_match = re.search(r'(?:###?\s*)?(?:处方|方药)[:：]?\s*(.*?)(?=\n#{1,3}|\Z)', content, re.DOTALL)
        if prescription_match:
            pre_text = prescription_match.group(1).strip()
            case.prescription = [p.strip() for p in re.split(r'[，。；;\n]', pre_text) if p.strip()]

        # 提取标签
        tag_match = re.search(r'(?:标签|Tags)[:：]\s*(.+)$', content, re.MULTILINE)
        if tag_match:
            case.tags = [t.strip() for t in tag_match.group(1).split(',') if t.strip()]

        return case

    def generate_knowledge_card(self, case):
        """生成知识卡片"""
        card = {
            'id': case.id,
            'title': case.title,
            'doctor': case.doctor,
            'diagnosis': case.diagnosis,
            'prescription': case.prescription,
            'key_symptoms': case.symptoms,
            'tongue_pulse': case.tongue_pulse,
            'tags': case.tags,
            'learning_notes': "",
            'mastery_level': 0
        }
        return card

    def save_to_markdown(self, case, output_dir):
        """保存为markdown格式"""
        md_content = f"""# {case.title}

## 患者信息
- 性别: {case.patient_info.get('gender', '')}
- 年龄: {case.patient_info.get('age', '')}
- 职业: {case.patient_info.get('occupation', '')}

## 症状
{chr(10).join(f'- {s}' for s in case.symptoms)}

## 舌脉
- 舌象: {case.tongue_pulse.get('tongue', '')}
- 脉象: {case.tongue_pulse.get('pulse', '')}

## 诊断
{case.diagnosis}

## 处方
{chr(10).join(f'- {p}' for p in case.prescription)}

---
*来源: {case.source}*
*医家: {case.doctor}*
*标签: {', '.join(case.tags)}*
"""

        filepath = os.path.join(output_dir, f"{case.id}.md")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)

        return filepath

    def process_all_cases(self):
        """处理所有医案"""
        print("=" * 50)
        print("中医温病医案处理工具")
        print("=" * 50)
        print()

        files = [f for f in os.listdir(self.raw_dir) if f.endswith('.md')]

        if not files:
            print("医案库为空，请先添加医案！")
            print(f"医案库位置: {self.raw_dir}")
            return

        print(f"找到 {len(files)} 个医案\n")

        for filename in files:
            filepath = os.path.join(self.raw_dir, filename)
            print(f"处理: {filename}")

            try:
                case = self.parse_markdown(filepath)
                print(f"  标题: {case.title}")
                print(f"  医家: {case.doctor}")
                print(f"  症状: {len(case.symptoms)} 个")

                # 保存已处理的
                self.save_to_markdown(case, self.processed_dir)
                print(f"  [OK] 已保存到 已学习 目录")

                # 生成知识卡片
                card = self.generate_knowledge_card(case)
                card_path = os.path.join(self.knowledge_dir, f"{case.id}.json")
                with open(card_path, 'w', encoding='utf-8') as f:
                    json.dump(card, f, ensure_ascii=False, indent=2)
                print(f"  [OK] 已生成知识卡片")

                print()

            except Exception as e:
                print(f"  [ERROR] 处理失败: {e}\n")

        print("=" * 50)
        print("处理完成！")
        print("=" * 50)

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
    processor = MedicalCaseProcessor(base_dir)

    print("=" * 50)
    print("中医温病医案处理工具")
    print("=" * 50)
    print()
    print("1. 处理所有医案")
    print("2. 生成医案模板")
    print("3. 退出")
    print()

    choice = input("请选择 (1-3): ").strip()

    if choice == "1":
        processor.process_all_cases()
    elif choice == "2":
        template = create_template()
        template_path = os.path.join(base_dir, "医案库", "00-医案模板.md")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template)
        print(f"✓ 模板已生成: {template_path}")
    else:
        print("再见！")

    input("\n按回车键退出...")

if __name__ == "__main__":
    main()
