from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    扩展Django默认用户模型
    """
    # 添加自定义字段
    is_teacher = models.BooleanField(default=False)
    school = models.CharField(max_length=100, blank=True, null=True)
    major = models.CharField(max_length=100, blank=True, null=True)
    join_date = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        
    def __str__(self):
        return self.username