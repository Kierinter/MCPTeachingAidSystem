from django.db import models
from users.models import User  # 更新导入路径

class CheckInRecord(models.Model):
    """签到记录模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='check_in_records', verbose_name="用户")
    check_in_date = models.DateField(auto_now_add=True, verbose_name="签到日期")
    check_in_time = models.DateTimeField(auto_now_add=True, verbose_name="签到时间")
    check_in_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="签到IP")
    notes = models.TextField(blank=True, null=True, verbose_name="备注")
    
    class Meta:
        verbose_name = "签到记录"
        verbose_name_plural = "签到记录"
        unique_together = ('user', 'check_in_date')  # 每个用户每天只能签到一次
        
    def __str__(self):
        return f"{self.user.username} - {self.check_in_date}"