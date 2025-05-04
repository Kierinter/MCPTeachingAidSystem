from django.db import models
from django.utils import timezone
from django.conf import settings

class Course(models.Model):
    """课程模型"""
    name = models.CharField(max_length=100, verbose_name="课程名称")
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='teaching_courses',
        verbose_name="授课教师"
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='enrolled_courses',
        verbose_name="选课学生"
    )
    location = models.CharField(max_length=100, verbose_name="上课地点")
    time_start = models.TimeField(verbose_name="上课时间")
    time_end = models.TimeField(verbose_name="下课时间")
    week_days = models.CharField(max_length=20, verbose_name="上课日期", 
                               help_text="以逗号分隔的数字，代表星期几，例如1,3,5")
    
    class Meta:
        verbose_name = "课程"
        verbose_name_plural = "课程"
        
    def __str__(self):
        return self.name
    
    def get_student_count(self):
        """获取学生人数"""
        return self.students.count()
    
    def is_today_class(self):
        """判断今天是否有课"""
        today_weekday = timezone.now().weekday() + 1  # 0是星期一，转换为1-7
        week_days_list = [int(day) for day in self.week_days.split(',')]
        return today_weekday in week_days_list


class CheckIn(models.Model):
    """签到活动模型"""
    STATUS_CHOICES = (
        ('active', '进行中'),
        ('expired', '已结束'),
        ('cancelled', '已取消'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="课程")
    check_in_code = models.CharField(max_length=6, verbose_name="签到码")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    expires_at = models.DateTimeField(verbose_name="过期时间")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name="状态")
    description = models.TextField(blank=True, verbose_name="签到说明")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_checkins',
        verbose_name="创建者"
    )
    
    class Meta:
        verbose_name = "签到活动"
        verbose_name_plural = "签到活动"
        
    def __str__(self):
        return f"{self.course.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def is_active(self):
        """判断签到是否有效"""
        now = timezone.now()
        return self.status == 'active' and now < self.expires_at
    
    def get_time_left(self):
        """获取剩余时间（秒）"""
        if not self.is_active():
            return 0
        now = timezone.now()
        return (self.expires_at - now).total_seconds()


class StudentCheckIn(models.Model):
    """学生签到记录模型"""
    STATUS_CHOICES = (
        ('success', '正常'),
        ('late', '迟到'),
        ('absent', '缺勤'),
    )
    
    check_in = models.ForeignKey(CheckIn, on_delete=models.CASCADE, verbose_name="签到活动")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='checkin_records',
        verbose_name="学生"
    )
    check_in_time = models.DateTimeField(auto_now_add=True, verbose_name="签到时间")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='success', verbose_name="状态")
    notes = models.TextField(blank=True, verbose_name="备注")
    location = models.CharField(max_length=200, blank=True, verbose_name="签到位置")
    
    class Meta:
        verbose_name = "学生签到记录"
        verbose_name_plural = "学生签到记录"
        # 确保一个学生在一次签到活动中只有一条记录
        unique_together = ('check_in', 'student')
        
    def __str__(self):
        # 显示学生真实姓名而不是username
        return f"{self.student.real_name} - {self.check_in_time.strftime('%Y-%m-%d %H:%M')}"