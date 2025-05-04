import os
import json
import pandas as pd
from django.core.management.base import BaseCommand
from problems.models import Subject, Topic, Problem

class Command(BaseCommand):
    help = '从JSON或CSV文件导入高中物理题目'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='JSON或CSV文件的路径')
        parser.add_argument('--format', type=str, default='json', help='文件格式(json或csv)')

    def handle(self, *args, **options):
        file_path = options['file_path']
        file_format = options['format'].lower()
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'文件不存在: {file_path}'))
            return
        try:
            # 获取或创建物理学科
            physics_subject, _ = Subject.objects.get_or_create(
                name='物理',
                defaults={'description': '高中物理'}
            )
            if file_format == 'csv':
                df = pd.read_csv(file_path, encoding='utf-8')
                problems_data = df.to_dict(orient='records')
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    problems_data = json.load(f)
            imported_count = 0
            topics_set = set()
            for item in problems_data:
                topic_name = item.get('知识点', '未分类')
                topics_set.add(topic_name)
                topic, _ = Topic.objects.get_or_create(
                    subject=physics_subject,
                    name=topic_name
                )
                problem = Problem(
                    topic=topic,
                    title=item.get('题目', '')[:255],
                    content=item.get('题目', ''),
                    answer=item.get('答案', ''),
                    explanation=item.get('解析', ''),
                    difficulty=item.get('难度', '中等')
                )
                problem.save()
                imported_count += 1
            self.stdout.write(self.style.SUCCESS(f'成功导入 {imported_count} 道物理题目'))
            self.stdout.write(self.style.SUCCESS(f'涉及知识点: {len(topics_set)} 个'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'导入失败: {str(e)}'))