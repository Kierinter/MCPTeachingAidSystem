from django.db import models
from django.conf import settings
from django.utils import timezone

class StudentProfile(models.Model):
    """学生详细信息模型"""
    ACADEMIC_LEVEL_CHOICES = (
        ('excellent', '优秀'),
        ('good', '良好'),
        ('average', '中等'),
        ('below_average', '中下'),
        ('poor', '薄弱'),
    )
    
    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        verbose_name="学生"
    )
    student_number = models.CharField(max_length=20, unique=True, verbose_name="学号")
    addmisson_year = models.CharField(max_length=20, blank=True, verbose_name="入学年份")
    grade = models.CharField(max_length=50, blank=True, verbose_name="年级")
    class_name = models.CharField(max_length=50, blank=True, verbose_name="班级")
    academic_level = models.CharField(
        max_length=20,
        choices=ACADEMIC_LEVEL_CHOICES,
        default='average',
        verbose_name="学业水平"
    )
    weak_subjects = models.TextField(blank=True, verbose_name="薄弱学科", help_text="以逗号分隔多个学科")
    notes = models.TextField(blank=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "学生档案"
        verbose_name_plural = "学生档案"
        
    def __str__(self):
        return f"{self.student.username} - {self.student_number}"
    
    def get_weak_subjects_list(self):
        """返回薄弱学科列表"""
        if not self.weak_subjects:
            return []
        return [subject.strip() for subject in self.weak_subjects.split(',')]


class AcademicRecord(models.Model):
    """学生学习记录模型"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='academic_records',
        verbose_name="学生"
    )
    subject = models.CharField(max_length=50, verbose_name="学科")
    score = models.FloatField(verbose_name="分数")
    semester = models.CharField(max_length=20, verbose_name="学期")
    exam_type = models.CharField(max_length=50, verbose_name="考试类型")
    exam_date = models.DateField(verbose_name="考试日期")
    remarks = models.TextField(blank=True, verbose_name="评语")
    
    class Meta:
        verbose_name = "学习记录"
        verbose_name_plural = "学习记录"
        
    def __str__(self):
        return f"{self.student.username} - {self.subject} ({self.semester})"


class ClassWork(models.Model):
    """课堂作业模型"""
    title = models.CharField(max_length=100, verbose_name="作业标题")
    description = models.TextField(blank=True, verbose_name="作业描述")
    class_name = models.CharField(max_length=50, verbose_name="班级")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_classworks',
        verbose_name="布置教师"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="布置时间")
    deadline = models.DateTimeField(verbose_name="截止时间")

    class Meta:
        verbose_name = "课堂作业"
        verbose_name_plural = "课堂作业"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.class_name} - {self.title}"

class StudentWork(models.Model):
    """学生作业提交模型"""
    classwork = models.ForeignKey(ClassWork, on_delete=models.CASCADE, related_name='submissions', verbose_name="课堂作业")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_works', verbose_name="学生")
    content = models.TextField(verbose_name="作业内容")
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="提交时间")
    score = models.FloatField(null=True, blank=True, verbose_name="分数")
    feedback = models.TextField(blank=True, verbose_name="教师评语")

    class Meta:
        verbose_name = "学生作业提交"
        verbose_name_plural = "学生作业提交"
        unique_together = ('classwork', 'student')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.username} - {self.classwork.title}"