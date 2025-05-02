from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """用户模型"""
    ROLE_CHOICES = [
        ('student', '学生'),
        ('teacher', '教师'),
    ]
    
    # username字段由AbstractUser提供
    # password字段由AbstractUser提供
    real_name = models.CharField(max_length=100, verbose_name="姓名")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student', verbose_name="身份")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"
    
    def __str__(self):
        return f"{self.username} - {self.real_name} ({self.get_role_display()})"