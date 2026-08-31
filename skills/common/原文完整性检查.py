# -*- coding: utf-8 -*-
"""
中医学习系统 - 原文完整性检查脚本
验证核心原文和参考资料的完整性
"""
import os
import re
from datetime import datetime

# 基础路径（动态计算：脚本位于 skills/common/，知识库在其上两级）
_BASE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(_BASE)), "00-原著全文")
SKILLS_DIR = os.path.dirname(os.path.dirname(_BASE))


def check_file_exists(path):
    """检查文件是否存在"""
    return os.path.exists(path) and os.path.isfile(path)


def get_file_size(path):
    """获取文件大小（KB）"""
    return round(os.path.getsize(path) / 1024, 1) if check_file_exists(path) else 0


def check_shanghan_integrity():
    """检查伤寒论完整性"""
    path = os.path.join(BASE_DIR, "伤寒论类", "伤寒论_完整版.txt")
    result = {"name": "伤寒论完整版", "path": path, "checks": []}
    
    if not check_file_exists(path):
        result["checks"].append(("文件存在", False, "文件不存在"))
        return result
    
    size_kb = get_file_size(path)
    result["checks"].append(("文件存在", True, f"{size_kb} KB"))
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查22篇结构
    chapters = re.findall(r'【(.+?第[一二三四五六七八九十百]+)】', content)
    chapter_count = len(chapters)
    result["checks"].append(("22篇结构", chapter_count == 22, f"发现 {chapter_count} 篇"))
    
    # 检查关键篇章
    key_chapters = ["太阳病", "阳明病", "少阳病", "太阴病", "少阴病", "厥阴病"]
    for ch in key_chapters:
        found = ch in content
        result["checks"].append((f"含{ch}篇", found, "存在" if found else "缺失"))
    
    # 检查是否有明显的截断（文件末尾是否有完整标点）
    tail = content[-200:] if len(content) > 200 else content
    tail_ok = any(tail.endswith(x) for x in ['。', '」', '】', '\n', ' '])
    result["checks"].append(("文件尾部完整", tail_ok, "末尾有正常结束" if tail_ok else "可能截断"))
    
    return result


def check_jingui_integrity():
    """检查金匮要略完整性"""
    path = os.path.join(BASE_DIR, "金匮要略类", "金匮要略_完整版.txt")
    result = {"name": "金匮要略完整版", "path": path, "checks": []}
    
    if not check_file_exists(path):
        result["checks"].append(("文件存在", False, "文件不存在"))
        return result
    
    size_kb = get_file_size(path)
    result["checks"].append(("文件存在", True, f"{size_kb} KB"))
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查22篇结构（第一篇"脏腑经络先后病脉证第一"无"并治"）
    chapters = re.findall(r'^(.+?脉证.*?第[一二三四五六七八九十]+)', content, re.MULTILINE)
    chapter_count = len(chapters)
    result["checks"].append(("22篇结构", chapter_count == 22, f"发现 {chapter_count} 篇：{', '.join(chapters[:3])}..."))
    
    # 检查关键篇章
    key_chapters = ["脏腑经络", "痉湿暍", "胸痹", "痰饮", "水气", "黄疸", "妇人"]
    for ch in key_chapters:
        found = ch in content
        result["checks"].append((f"含{ch}篇", found, "存在" if found else "缺失"))
    
    # 检查尾部
    tail = content[-200:] if len(content) > 200 else content
    tail_ok = any(tail.endswith(x) for x in ['。', '」', '】', '\n', ' '])
    result["checks"].append(("文件尾部完整", tail_ok, "末尾有正常结束" if tail_ok else "可能截断"))
    
    return result


def check_medical_cases():
    """检查医案文件"""
    cases = [
        ("经方实验录", "医案类", "经方实验录.txt", 100),
        ("胡希恕医论医案集粹", "医案类", "胡希恕医论医案集粹.txt", 100),
        ("刘渡舟验案精选", "医案类", "刘渡舟验案精选.txt", 100),
        ("王孟英医案绎注", "医案类", "王孟英医案绎注.txt", 100),
        ("临证指南医案", "医案类", "临证指南医案.txt", 100),
        ("吴鞠通医案", "医案类", "吴鞠通医案.txt", 100),
        ("丁甘仁医案", "医案类", "丁甘仁医案.txt", 100),
    ]
    
    results = []
    for name, subdir, filename, min_kb in cases:
        path = os.path.join(BASE_DIR, subdir, filename)
        result = {"name": name, "path": path, "checks": []}
        
        if not check_file_exists(path):
            result["checks"].append(("文件存在", False, "文件不存在"))
            results.append(result)
            continue
        
        size_kb = get_file_size(path)
        result["checks"].append(("文件存在", True, f"{size_kb} KB"))
        result["checks"].append(("大小合理", size_kb >= min_kb, f"{size_kb} KB (最低{min_kb} KB)"))
        
        # 检查是否为空或只有HTML
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read(500)
        
        is_html = '<html' in content.lower() or '<!doctype' in content.lower()
        result["checks"].append(("非HTML", not is_html, "是HTML文件" if is_html else "纯文本"))
        
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', content))
        result["checks"].append(("含中文内容", has_chinese, "有中文" if has_chinese else "无中文"))
        
        results.append(result)
    
    return results


def check_lectures():
    """检查讲稿文件"""
    lectures = [
        ("刘渡舟伤寒论讲稿", "伤寒论类", "刘渡舟伤寒论讲稿.txt", 50),
        ("郝万山讲伤寒论", "伤寒论类", "郝万山讲伤寒论.txt", 50),
    ]
    
    results = []
    for name, subdir, filename, min_kb in lectures:
        path = os.path.join(BASE_DIR, subdir, filename)
        result = {"name": name, "path": path, "checks": []}
        
        if not check_file_exists(path):
            result["checks"].append(("文件存在", False, "文件不存在"))
            results.append(result)
            continue
        
        size_kb = get_file_size(path)
        result["checks"].append(("文件存在", True, f"{size_kb} KB"))
        result["checks"].append(("大小合理", size_kb >= min_kb, f"{size_kb} KB (最低{min_kb} KB)"))
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read(500)
        
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', content))
        result["checks"].append(("含中文内容", has_chinese, "有中文" if has_chinese else "无中文"))
        
        results.append(result)
    
    return results


def print_report(results_list):
    """打印检查报告"""
    print("=" * 70)
    print(f"中医学习系统 - 原文完整性检查报告")
    print(f"检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    total_checks = 0
    passed_checks = 0
    
    for result in results_list:
        if isinstance(result, list):
            for r in result:
                print(f"\n【{r['name']}】")
                print(f"  路径：{r['path']}")
                for check_name, passed, detail in r['checks']:
                    status = "通过" if passed else "失败"
                    symbol = "  " if passed else "!!"
                    print(f"  {symbol} {check_name}: {status} ({detail})")
                    total_checks += 1
                    if passed:
                        passed_checks += 1
        else:
            print(f"\n【{result['name']}】")
            print(f"  路径：{result['path']}")
            for check_name, passed, detail in result['checks']:
                status = "通过" if passed else "失败"
                symbol = "  " if passed else "!!"
                print(f"  {symbol} {check_name}: {status} ({detail})")
                total_checks += 1
                if passed:
                    passed_checks += 1
    
    print("\n" + "=" * 70)
    print(f"总计：{passed_checks}/{total_checks} 项检查通过")
    print(f"通过率：{passed_checks/total_checks*100:.1f}%")
    print("=" * 70)
    
    return passed_checks == total_checks


def main():
    """主函数"""
    print("开始检查原文完整性...\n")
    
    results = []
    
    # 检查伤寒论
    print("检查伤寒论...")
    results.append(check_shanghan_integrity())
    
    # 检查金匮要略
    print("检查金匮要略...")
    results.append(check_jingui_integrity())
    
    # 检查医案
    print("检查医案文件...")
    results.append(check_medical_cases())
    
    # 检查讲稿
    print("检查讲稿文件...")
    results.append(check_lectures())
    
    # 打印报告
    all_passed = print_report(results)
    
    if all_passed:
        print("\n全部检查通过！")
        return 0
    else:
        print("\n部分检查未通过，请查看上方报告。")
        return 1


if __name__ == '__main__':
    exit(main())
