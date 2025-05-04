from rest_framework import serializers
from django.utils import timezone
from .models import CheckIn, StudentCheckIn

class CheckInSerializer(serializers.ModelSerializer):
    """签到活动序列化器"""
    is_active = serializers.SerializerMethodField()
    time_left = serializers.SerializerMethodField()
    
    class Meta:
        model = CheckIn
        fields = ['id', 'check_in_code', 'created_at', 
                  'expires_at', 'status', 'description', 'is_active', 'time_left']
        extra_kwargs = {
            'check_in_code': {'write_only': True}
        }
    
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
    
    def validate_check_in_code(self, value):
        if not value.isalnum() or len(value) != 6:
            raise serializers.ValidationError("签到码必须是6位数字或字母")
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        # 这里假设课程校验已在视图层完成
        from .models import Course
        course = Course.objects.get(id=validated_data['course_id'])
        expires_at = timezone.now() + timezone.timedelta(minutes=validated_data['valid_minutes'])
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
    student_name = serializers.SerializerMethodField()
    check_in_time_display = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentCheckIn
        fields = ['id', 'student', 'student_name', 'check_in', 
                  'check_in_time', 'check_in_time_display', 'status', 'notes', 'location']
    
    def get_student_name(self, obj):
        return obj.student.real_name or obj.student.username
    
    def get_check_in_time_display(self, obj):
        return obj.check_in_time.strftime('%Y-%m-%d %H:%M:%S')

class StudentCheckInSubmitSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    check_in_code = serializers.CharField(max_length=6)
    location = serializers.CharField(max_length=200, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        user = self.context['request'].user
        course_id = data.get('course_id')
        check_in_code = data.get('check_in_code')
        from .models import Course
        try:
            course = Course.objects.get(id=course_id)
            if not course.students.filter(id=user.id).exists():
                raise serializers.ValidationError({"course_id": "您不是该课程的学生"})
        except Course.DoesNotExist:
            raise serializers.ValidationError({"course_id": "课程不存在"})
        try:
            check_in = CheckIn.objects.get(
                course_id=course_id,
                check_in_code=check_in_code,
                status='active',
                expires_at__gt=timezone.now()
            )
            self.context['check_in'] = check_in
        except CheckIn.DoesNotExist:
            raise serializers.ValidationError({"check_in_code": "签到码无效或已过期"})
        if StudentCheckIn.objects.filter(check_in=check_in, student=user).exists():
            raise serializers.ValidationError({"check_in_code": "您已经签到过了"})
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        check_in = self.context['check_in']
        status = 'success'
        course_time_start = check_in.course.time_start
        now_time = timezone.localtime(timezone.now()).time()
        today = timezone.localtime(timezone.now()).date()
        course_start_datetime = timezone.datetime.combine(
            today, 
            course_time_start,
            tzinfo=timezone.get_current_timezone()
        )
        late_threshold = course_start_datetime + timezone.timedelta(minutes=10)
        if timezone.localtime(timezone.now()) > late_threshold:
            status = 'late'
        student_check_in = StudentCheckIn.objects.create(
            check_in=check_in,
            student=user,
            status=status,
            notes=validated_data.get('notes', ''),
            location=validated_data.get('location', '')
        )
        return student_check_in

class CheckInHistorySerializer(serializers.ModelSerializer):
    check_in_time = serializers.SerializerMethodField()
    status = serializers.CharField(source='status')
    location = serializers.CharField(source='location')
    
    class Meta:
        model = StudentCheckIn
        fields = ['id', 'check_in_time', 'status', 'location']
    
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