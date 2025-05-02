from django.db import models
from users.models import User  # 修改导入路径

class Subject(models.Model):
    """学科分类"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Topic(models.Model):
    """知识点分类"""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.subject.name} - {self.name}"

class Problem(models.Model):
    """题目模型"""
    DIFFICULTY_CHOICES = [
        ('简单', '简单'),
        ('中等', '中等'),
        ('较难', '较难'),
        ('困难', '困难'),
    ]
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='problems')
    title = models.CharField(max_length=255)
    content = models.TextField()
    answer = models.TextField()
    explanation = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.topic.name} - {self.title[:30]}"

class UserProblemRecord(models.Model):
    """用户题目作答记录"""
    STATUS_CHOICES = [
        ('correct', '正确'),
        ('incorrect', '错误'),
        ('partially_correct', '部分正确'),
        ('skipped', '跳过'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='problem_records')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='user_records')
    user_answer = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    score = models.FloatField(default=0)  # 得分(0-100)
    time_spent = models.IntegerField(default=0)  # 花费时间(秒)
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'problem')  # 每个用户对每道题只有一条最新记录