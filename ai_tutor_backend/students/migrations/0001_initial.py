# Generated by Django 5.2 on 2025-05-03 14:54

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AcademicRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=50, verbose_name='学科')),
                ('score', models.FloatField(verbose_name='分数')),
                ('semester', models.CharField(max_length=20, verbose_name='学期')),
                ('exam_type', models.CharField(max_length=50, verbose_name='考试类型')),
                ('exam_date', models.DateField(verbose_name='考试日期')),
                ('remarks', models.TextField(blank=True, verbose_name='评语')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='academic_records', to=settings.AUTH_USER_MODEL, verbose_name='学生')),
            ],
            options={
                'verbose_name': '学习记录',
                'verbose_name_plural': '学习记录',
            },
        ),
        migrations.CreateModel(
            name='StudentProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_number', models.CharField(max_length=20, unique=True, verbose_name='学号')),
                ('grade', models.CharField(blank=True, max_length=20, verbose_name='年级')),
                ('major', models.CharField(blank=True, max_length=50, verbose_name='专业')),
                ('class_name', models.CharField(blank=True, max_length=50, verbose_name='班级')),
                ('academic_level', models.CharField(choices=[('excellent', '优秀'), ('good', '良好'), ('average', '中等'), ('below_average', '中下'), ('poor', '薄弱')], default='average', max_length=20, verbose_name='学业水平')),
                ('weak_subjects', models.TextField(blank=True, help_text='以逗号分隔多个学科', verbose_name='薄弱学科')),
                ('notes', models.TextField(blank=True, verbose_name='备注')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='student_profile', to=settings.AUTH_USER_MODEL, verbose_name='学生')),
            ],
            options={
                'verbose_name': '学生档案',
                'verbose_name_plural': '学生档案',
            },
        ),
    ]
