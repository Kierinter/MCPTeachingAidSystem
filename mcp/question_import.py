import os
import json
import pandas as pd
from django.core.management.base import BaseCommand
from ai_tutor_backend.problems.models import Subject, Topic, Problem

class Command(BaseCommand):
    help = '从JSON或CSV文件导入题目到数据库'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='题目数据文件路径')
        parser.add_argument('--format', type=str, default='json', help='文件格式(json或csv)')

    def handle(self, *args, **options):
        file_path = options['file_path']
        file_format = options['format'].lower()
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'文件不存在: {file_path}'))
            return
        
        try:
            if file_format == 'json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    problems_data = json.load(f)
            elif file_format == 'csv':
                df = pd.read_csv(file_path)
                problems_data = df.to_dict('records')
            else:
                self.stdout.write(self.style.ERROR('不支持的文件格式，请使用json或csv'))
                return
                
            # 统计导入数量
            imported_count = 0
            
            # 创建默认学科 - 可以根据实际情况调整
            math_subject, _ = Subject.objects.get_or_create(name='数学')
            
            for item in problems_data:
                # 根据知识点创建或获取Topic
                topic_name = item.get('知识点', '未分类')
                topic, _ = Topic.objects.get_or_create(
                    subject=math_subject,
                    name=topic_name
                )
                
                # 创建题目
                problem = Problem(
                    topic=topic,
                    title=item.get('题目', '')[:255],  # 截断标题以适应字段长度
                    content=item.get('题目', ''),
                    answer=item.get('答案', ''),
                    explanation=item.get('解析', ''),
                    difficulty=item.get('难度', '中等')
                )
                problem.save()
                imported_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'成功导入 {imported_count} 道题目'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'导入失败: {str(e)}'))