from rest_framework import serializers
from django.utils import timezone
from .models import Course, CheckIn, StudentCheckIn


class CourseSerializer(serializers.ModelSerializer):
    """课程序列化器"""
    teacher_name = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = ['id', 'name', 'teacher', 'teacher_name', 'location', 
                  'time_start', 'time_end', 'week_days', 'student_count']
    
    def get_teacher_name(self, obj):
        return obj.teacher.get_full_name() or obj.teacher.username
    
    def get_student_count(self, obj):
        return obj.get_student_count()


class CheckInSerializer(serializers.ModelSerializer):
    """签到活动序列化器"""
    course_name = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    time_left = serializers.SerializerMethodField()
    
    class Meta:
        model = CheckIn
        fields = ['id', 'course', 'course_name', 'check_in_code', 'created_at', 
                  'expires_at', 'status', 'description', 'is_active', 'time_left']
        extra_kwargs = {
            'check_in_code': {'write_only': True}  # 签到码只写，不在列表中显示
        }
    
    def get_course_name(self, obj):
        return obj.course.name
    
    def get_is_active(self, obj):
        return obj.is_active()
    
    def get_time_left(self, obj):
        return obj.get_time_left()


class CheckInCreateSerializer(serializers.Serializer):
    """创建签到的序列化器"""
    course_id = serializers.IntegerField()
    check_in_code = serializers.CharField(max_length=6)
    valid_minutes = serializers.IntegerField(min_value=1, max_value=180)
    description = serializers.CharField(allow_blank=True, required=False)
    
    def validate_course_id(self, value):
        """验证课程存在且当前用户是该课程的老师"""
        user = self.context['request'].user
        try:
            course = Course.objects.get(id=value, teacher=user)
            return value
        except Course.DoesNotExist:
            raise serializers.ValidationError("课程不存在或您不是该课程的教师")
    
    def validate_check_in_code(self, value):
        """验证签到码格式"""
        if not value.isalnum() or len(value) != 6:
            raise serializers.ValidationError("签到码必须是6位数字或字母")
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        course = Course.objects.get(id=validated_data['course_id'])
        
        # 计算过期时间
        expires_at = timezone.now() + timezone.timedelta(minutes=validated_data['valid_minutes'])
        
        # 创建签到活动
        check_in = CheckIn.objects.create(
            course=course,
            check_in_code=validated_data['check_in_code'],
            expires_at=expires_at,
            status='active',
            description=validated_data.get('description', ''),
            created_by=user
        )
        
        return check_in


class StudentCheckInSerializer(serializers.ModelSerializer):
    """学生签到记录序列化器"""
    student_name = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()
    check_in_time_display = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentCheckIn
        fields = ['id', 'student', 'student_name', 'check_in', 'course_name', 
                  'check_in_time', 'check_in_time_display', 'status', 'notes', 'location']
    
    def get_student_name(self, obj):
        # 优先显示学生真实姓名（real_name），否则显示username
        return obj.student.real_name or obj.student.username
    
    def get_course_name(self, obj):
        return obj.check_in.course.name
    
    def get_check_in_time_display(self, obj):
        return obj.check_in_time.strftime('%Y-%m-%d %H:%M:%S')


class StudentCheckInSubmitSerializer(serializers.Serializer):
    """学生提交签到的序列化器"""
    course_id = serializers.IntegerField()
    check_in_code = serializers.CharField(max_length=6)
    location = serializers.CharField(max_length=200, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """验证签到码是否正确且有效"""
        user = self.context['request'].user
        course_id = data.get('course_id')
        check_in_code = data.get('check_in_code')
        
        # 验证课程是否存在且学生已选课
        try:
            course = Course.objects.get(id=course_id)
            if not course.students.filter(id=user.id).exists():
                raise serializers.ValidationError({"course_id": "您不是该课程的学生"})
        except Course.DoesNotExist:
            raise serializers.ValidationError({"course_id": "课程不存在"})
        
        # 验证是否存在有效的签到活动
        try:
            check_in = CheckIn.objects.get(
                course_id=course_id,
                check_in_code=check_in_code,
                status='active',
                expires_at__gt=timezone.now()
            )
            # 将check_in对象存储以便create方法使用
            self.context['check_in'] = check_in
        except CheckIn.DoesNotExist:
            raise serializers.ValidationError({"check_in_code": "签到码无效或已过期"})
            
        # 检查学生是否已签到
        if StudentCheckIn.objects.filter(check_in=check_in, student=user).exists():
            raise serializers.ValidationError({"check_in_code": "您已经签到过了"})
            
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        check_in = self.context['check_in']
        
        # 默认状态为正常签到
        status = 'success'
        
        # 判断是否迟到 (如果课程开始时间+10分钟后签到则为迟到)
        course_time_start = check_in.course.time_start
        now_time = timezone.localtime(timezone.now()).time()
        
        # 创建一个今天的日期与课程开始时间组合的datetime对象
        today = timezone.localtime(timezone.now()).date()
        course_start_datetime = timezone.datetime.combine(
            today, 
            course_time_start,
            tzinfo=timezone.get_current_timezone()
        )
        
        # 计算允许迟到的时间点 (课程开始后10分钟)
        late_threshold = course_start_datetime + timezone.timedelta(minutes=10)
        
        # 如果当前时间超过了允许迟到的时间，标记为迟到
        if timezone.localtime(timezone.now()) > late_threshold:
            status = 'late'
        
        # 创建签到记录
        student_check_in = StudentCheckIn.objects.create(
            check_in=check_in,
            student=user,
            status=status,
            notes=validated_data.get('notes', ''),
            location=validated_data.get('location', '')
        )
        
        return student_check_in


class ActiveCourseSerializer(serializers.ModelSerializer):
    """当前活动课程序列化器（包含签到信息）"""
    teacher_name = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    check_in_code = serializers.SerializerMethodField()
    expires_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = ['id', 'name', 'teacher_name', 'location', 
                  'time_start', 'time_end', 'is_active',
                  'check_in_code', 'expires_at']
    
    def get_teacher_name(self, obj):
        return obj.teacher.get_full_name() or obj.teacher.username
    
    def get_is_active(self, obj):
        # 查找该课程是否有活跃的签到
        active_check_in = CheckIn.objects.filter(
            course=obj,
            status='active',
            expires_at__gt=timezone.now()
        ).first()
        return active_check_in is not None
    
    def get_check_in_code(self, obj):
        # 仅对教师显示签到码
        user = self.context.get('request').user
        if user and user == obj.teacher:
            active_check_in = CheckIn.objects.filter(
                course=obj,
                status='active',
                expires_at__gt=timezone.now()
            ).first()
            if active_check_in:
                return active_check_in.check_in_code
        return None
    
    def get_expires_at(self, obj):
        active_check_in = CheckIn.objects.filter(
            course=obj,
            status='active',
            expires_at__gt=timezone.now()
        ).first()
        if active_check_in:
            return active_check_in.expires_at
        return None


class CheckInHistorySerializer(serializers.ModelSerializer):
    """签到历史记录序列化器（学生视角）"""
    course_name = serializers.SerializerMethodField()
    check_in_time = serializers.SerializerMethodField()
    status = serializers.CharField(source='status')
    location = serializers.CharField(source='location')
    
    class Meta:
        model = StudentCheckIn
        fields = ['id', 'course_name', 'check_in_time', 'status', 'location']
    
    def get_course_name(self, obj):
        return obj.check_in.course.name
    
    def get_check_in_time(self, obj):
        return obj.check_in_time.strftime('%Y-%m-%d %H:%M')


class TeacherCheckInDetailSerializer(serializers.ModelSerializer):
    """教师查看签到详情的序列化器"""
    course_name = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()
    checked_in_count = serializers.SerializerMethodField()
    late_count = serializers.SerializerMethodField()
    absent_count = serializers.SerializerMethodField()
    check_in_status = serializers.SerializerMethodField()
    time_left = serializers.SerializerMethodField()
    
    class Meta:
        model = CheckIn
        fields = ['id', 'course', 'course_name', 'check_in_code', 'created_at', 
                  'expires_at', 'status', 'total_students', 'checked_in_count', 
                  'late_count', 'absent_count', 'check_in_status', 'time_left']
    
    def get_course_name(self, obj):
        return obj.course.name
    
    def get_total_students(self, obj):
        return obj.course.students.count()
    
    def get_checked_in_count(self, obj):
        return StudentCheckIn.objects.filter(check_in=obj, status='success').count()
    
    def get_late_count(self, obj):
        return StudentCheckIn.objects.filter(check_in=obj, status='late').count()
    
    def get_absent_count(self, obj):
        # 计算缺勤人数，总人数减去已签到人数（无论是否迟到）
        total = obj.course.students.count()
        checked_in = StudentCheckIn.objects.filter(check_in=obj).count()
        return total - checked_in
    
    def get_check_in_status(self, obj):
        now = timezone.now()
        if obj.status == 'cancelled':
            return '已取消'
        elif now > obj.expires_at:
            return '已结束'
        else:
            return '进行中'
    
    def get_time_left(self, obj):
        if obj.is_active():
            return obj.get_time_left()
        return 0