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
        parser.add_argument('--subject', type=str, default='数学', help='学科名称')

    def handle(self, *args, **options):
        file_path = options['file_path']
        file_format = options['format'].lower()
        subject_name = options['subject']