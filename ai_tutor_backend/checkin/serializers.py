from rest_framework import serializers
from django.utils import timezone
from .models import CheckIn, StudentCheckIn

class CheckInSerializer(serializers.ModelSerializer):
    """签到活动序列化器"""
    is_active = serializers.SerializerMethodField()
    time_left = serializers.SerializerMethodField()
    
    class Meta:
        model = CheckIn
        fields = ['id', 'check_in_code', 'created_at', 'class_name',
                  'expires_at', 'status', 'description', 'is_active', 'time_left']
    
    def get_is_active(self, obj):
        return obj.is_active()
    
    def get_time_left(self, obj):
        return obj.get_time_left()

class CheckInCreateSerializer(serializers.Serializer):
    """创建签到的序列化器"""
    class_name = serializers.CharField(max_length=50)
    check_in_code = serializers.CharField(max_length=6)
    valid_minutes = serializers.IntegerField(min_value=1, max_value=180)
    description = serializers.CharField(allow_blank=True, required=False)
    
    def validate_check_in_code(self, value):
        if not value.isalnum() or len(value) != 6:
            raise serializers.ValidationError("签到码必须是6位数字或字母")
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        expires_at = timezone.now() + timezone.timedelta(minutes=validated_data['valid_minutes'])
        check_in = CheckIn.objects.create(
            class_name=validated_data['class_name'],
            check_in_code=validated_data['check_in_code'],
            expires_at=expires_at,
            status='active',
            description=validated_data.get('description', ''),
            created_by=user
        )
        return check_in

class StudentCheckInSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    check_in_time_display = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentCheckIn
        fields = ['id', 'student', 'student_name', 'class_name', 'check_in','check_in_time', 'check_in_time_display', 'status', 'notes', 'location']
    
    def get_student_name(self, obj):
        # 优先使用签到时提供的姓名，其次是用户的真实姓名，最后是用户名
        if obj.student_name:
            return obj.student_name
        return obj.student.real_name or obj.student.username
    
    def get_check_in_time_display(self, obj):
        return obj.check_in_time.strftime('%Y-%m-%d %H:%M:%S')

class StudentCheckInSubmitSerializer(serializers.Serializer):
    check_in_code = serializers.CharField(max_length=6)
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        user = self.context['request'].user
        check_in_code = data.get('check_in_code')
        
        if not check_in_code:
            raise serializers.ValidationError({"check_in_code": "签到码不能为空"})
        
        try:
            # 查找有效的签到活动
            check_in = CheckIn.objects.get(
                check_in_code=check_in_code,
                status='active',
                expires_at__gt=timezone.now()
            )
            self.context['check_in'] = check_in
        except CheckIn.DoesNotExist:
            raise serializers.ValidationError({"check_in_code": "签到码无效或已过期"})
        
        # 检查是否已签到
        if StudentCheckIn.objects.filter(check_in=check_in, student=user).exists():
            raise serializers.ValidationError({"check_in_code": "您已经签到过了"})
            
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        check_in = self.context['check_in']
        status = 'success'
        
        # 判断是否迟到
        now = timezone.now()
        # 签到创建时间加5分钟为正常签到时间
        normal_time_limit = check_in.created_at + timezone.timedelta(minutes=5)
        if now > normal_time_limit:
            status = 'late'
        
        # 获取学生姓名和班级信息
        student_name = user.real_name if hasattr(user, 'real_name') else user.username
        class_name = ''
        
        # 尝试从学生档案中获取班级信息
        try:
            from students.models import StudentProfile
            profile = StudentProfile.objects.get(student=user)
            class_name = profile.class_name
        except:
            # 如果获取失败，使用签到活动中的班级
            class_name = check_in.class_name
        
        # 创建签到记录
        student_check_in = StudentCheckIn.objects.create(
            check_in=check_in,
            student=user,
            student_name=student_name,
            class_name=class_name,
            status=status,
            notes=validated_data.get('notes', ''),
            location=validated_data.get('location', '')
        )
        return student_check_in

class CheckInHistorySerializer(serializers.ModelSerializer):
    check_in_time = serializers.SerializerMethodField()
    status = serializers.CharField(source='status')
    location = serializers.CharField(source='location')
    check_in_id = serializers.IntegerField(source='check_in.id')
    
    class Meta:
        model = StudentCheckIn
        fields = ['id', 'check_in_id', 'check_in_time', 'status', 'location']
    
    def get_check_in_time(self, obj):
        return obj.check_in_time.strftime('%Y-%m-%d %H:%M')

class TeacherCheckInDetailSerializer(serializers.ModelSerializer):
    total_students = serializers.SerializerMethodField()
    checked_in_count = serializers.SerializerMethodField()
    late_count = serializers.SerializerMethodField()
    absent_count = serializers.SerializerMethodField()
    check_in_status = serializers.SerializerMethodField()
    time_left = serializers.SerializerMethodField()
    
    class Meta:
        model = CheckIn
        fields = ['id', 'check_in_code', 'created_at', 
                  'expires_at', 'status', 'total_students', 'checked_in_count', 
                  'late_count', 'absent_count', 'check_in_status', 'time_left']
    
    def get_total_students(self, obj):
        return obj.course.students.count()
    def get_checked_in_count(self, obj):
        return StudentCheckIn.objects.filter(check_in=obj, status__in=['success', 'late']).count()
    def get_late_count(self, obj):
        return StudentCheckIn.objects.filter(check_in=obj, status='late').count()
    def get_absent_count(self, obj):
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