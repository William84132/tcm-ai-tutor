#!/usr/bin/env python3
"""
中医温病课程导师 - 主程序
负责学习进度追踪和课程内容管理
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class LearningProgress:
    """学习进度管理类"""
    
    def __init__(self, obsidian_root: str = "e:\\叶天士\\叶天士"):
        self.obsidian_root = obsidian_root
        self.progress_file = os.path.join(obsidian_root, "学习进度追踪.md")
        self.case_dir = os.path.join(obsidian_root, "06-临床医案", "案例分析")
        self.review_dir = os.path.join(obsidian_root, "07-伤寒论复习")
        
    def load_progress(self) -> Dict:
        """加载学习进度"""
        if not os.path.exists(self.progress_file):
            return self._create_default_progress()
        
        with open(self.progress_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析进度
        progress = {
            'completed_courses': 0,
            'completed_reviews': 0,
            'last_date': datetime.now().strftime('%Y-%m-%d'),
            'next_course': '',
            'weak_points': []
        }
        
        # 匹配已完成课程次数
        match = re.search(r'\*\*已完成课程次数\*\*\s*\|\s*(\d+)', content)
        if match:
            progress['completed_courses'] = int(match.group(1))
        
        # 匹配已完成复习次数
        match = re.search(r'\*\*已完成复习次数\*\*\s*\|\s*(\d+)', content)
        if match:
            progress['completed_reviews'] = int(match.group(1))
        
        # 匹配下一步课程
        match = re.search(r'\*\*下一步课程\*\*\s*\|\s*(.+?)\s*\|', content)
        if match:
            progress['next_course'] = match.group(1).strip()
        
        return progress
    
    def _create_default_progress(self) -> Dict:
        """创建默认进度"""
        return {
            'completed_courses': 0,
            'completed_reviews': 0,
            'last_date': datetime.now().strftime('%Y-%m-%d'),
            'next_course': '第一课（案例分析课）',
            'weak_points': []
        }
    
    def determine_next_course(self, progress: Dict) -> Tuple[str, str]:
        """
        确定下一步课程类型
        返回：(课程类型, 课程名称)
        课程类型：'case' | 'review' | 'comprehensive_review'
        """
        completed = progress['completed_courses']
        reviews = progress['completed_reviews']
        
        # 已完成6次课程但未完成综合复习
        if completed >= 6 and reviews == 0:
            return 'comprehensive_review', '综合复习课'
        
        # 已完成综合复习，继续案例课
        if reviews >= 1:
            next_num = completed + 1
            return 'case', f'第{next_num}课（案例分析课）'
        
        # 案例课与复习课交替
        # 根据现有课程模式：1(case), 2(review), 3(case), 4(review), 5(case), 6(case), 7(review), 8(case)
        course_pattern = {
            1: 'case', 2: 'review', 3: 'case', 4: 'review',
            5: 'case', 6: 'case', 7: 'review', 8: 'case'
        }
        
        next_num = completed + 1
        if next_num in course_pattern:
            course_type = course_pattern[next_num]
        else:
            # 默认交替
            course_type = 'case' if next_num % 2 == 1 else 'review'
        
        if course_type == 'case':
            return 'case', f'第{next_num}课（案例分析课）'
        else:
            return 'review', f'第{next_num}课（复习课）'


def get_welcome_message(progress: Dict, next_type: str, next_name: str) -> str:
    """生成欢迎消息"""
    message = f"欢迎回来！\n\n"
    message += f"## 学习进度\n"
    message += f"- 已完成课程：{progress['completed_courses']} 次\n"
    message += f"- 已完成复习：{progress['completed_reviews']} 次\n"
    message += f"- 这是您的第 {progress['completed_courses'] + 1} 次学习\n\n"
    message += f"## 本次课程\n"
    message += f"下一步：**{next_name}**\n\n"
    
    if next_type == 'case':
        message += "让我们开始今天的案例分析！\n"
    elif next_type == 'review':
        message += "让我们开始今天的复习课！\n"
    else:
        message += "让我们开始综合复习！\n"
    
    return message


if __name__ == "__main__":
    # 测试代码
    progress_manager = LearningProgress()
    progress = progress_manager.load_progress()
    next_type, next_name = progress_manager.determine_next_course(progress)
    print(get_welcome_message(progress, next_type, next_name))
