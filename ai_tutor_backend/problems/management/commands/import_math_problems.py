import os
import json
import pandas as pd
from django.core.management.base import BaseCommand
from problems.models import Subject, Topic, Problem

class Command(BaseCommand):
    help = '从JSON或CSV文件导入题目到数据库'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='题目数据文件路径')
        parser.add_argument('--format', type=str, default='json', help='文件格式(json或csv)')

    def handle(self, *args, **options):
        file_path = options['file_path']

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'文件不存在: {file_path}'))
            return

        try:
            english_subject, created = Subject.objects.get_or_create(
                name='数学',
                defaults={'description': '高中数学'}
            )

            # 读取JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                problems_data = json.load(f)

            imported_count = 0
            topics_set = set()  # 用于记录题目中出现的所有知识点

            for item in problems_data:
                # 根据知识点创建或获取Topic
                topic_name = item.get('知识点', '未分类')
                topics_set.add(topic_name)

                topic, _ = Topic.objects.get_or_create(
                    subject=english_subject,
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

            self.stdout.write(self.style.SUCCESS(f'成功导入 {imported_count} 道英语题目'))
            self.stdout.write(self.style.SUCCESS(f'涉及知识点: {len(topics_set)} 个'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'导入失败: {str(e)}'))
