from django.core.management.base import BaseCommand
from django.conf import settings
from users.models import User
from students.models import StudentProfile
import random

class Command(BaseCommand):
    help = '批量导入测试学生信息'

    def handle(self, *args, **options):
        COMMON_CHINESE_LAST_NAMES = [
            '张', '李', '王', '刘', '陈', '杨', '黄', '赵', '吴', '周', '徐', '孙', '马', '朱', '胡'
        ]
        COMMON_CHINESE_FIRST_NAME = [
            '伟', '芳', '娜', '敏', '静', '丽', '强', '磊', '军', '洋', '勇', '艳', '杰', '娟', '涛', '明', '超', '秀英', '霞', '平',
            '刚', '桂', '丹', '萍', '鑫', '鹏', '华', '玉兰', '玉梅', '莉', '玉珍', '玉英', '玉华', '玉荣', '玉珍', '玉娟', '玉芬'
        ]
        def random_name():
            first = random.choice(COMMON_CHINESE_LAST_NAMES)
            second = random.choice(COMMON_CHINESE_FIRST_NAME)
            return f"{first}{second}"

        STUDENT_LIST = [
            {
            'username': f'student{str(i+37).zfill(2)}',
            'real_name': random_name(),
            'student_number': f'202401{i:02d}',
            'grade': '2024级',
            'major': '高中二年级',
            'class_name': '2班',
            'academic_level': random.choice(['excellent', 'good', 'average', 'below_average', 'poor']),
            'weak_subjects': random.choice(['数学', '英语', '物理']),
            'notes': ''
            }
            for i in range(1, 36)
        ]
        for stu in STUDENT_LIST:
            user, created = User.objects.get_or_create(
                username=stu['username'],
                defaults={
                    'real_name': stu['real_name'],
                    'role': 'student',
                    'is_active': True
                }
            )
            if created:
                user.set_password('123456')
                user.save()
                self.stdout.write(self.style.SUCCESS(f"创建用户: {user.username}"))
            else:
                self.stdout.write(self.style.WARNING(f"用户已存在: {user.username}"))
            profile, _ = StudentProfile.objects.get_or_create(
                student=user,
                defaults={
                    'student_number': stu['student_number'],
                    'grade': stu['grade'],
                    'major': stu['major'],
                    'class_name': stu['class_name'],
                    'academic_level': stu['academic_level'],
                    'weak_subjects': stu['weak_subjects'],
                    'notes': stu['notes']
                }
            )
            self.stdout.write(f"学生档案: {profile.student_number} - {user.real_name}")
        self.stdout.write(self.style.SUCCESS('测试学生导入完成！'))