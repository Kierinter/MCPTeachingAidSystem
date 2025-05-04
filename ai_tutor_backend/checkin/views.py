from rest_framework import viewsets, generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Course, CheckIn, StudentCheckIn
from .serializers import (
    CourseSerializer, 
    CheckInSerializer, 
    CheckInCreateSerializer, 
    StudentCheckInSerializer,
    StudentCheckInSubmitSerializer,
    ActiveCourseSerializer,
    CheckInHistorySerializer,
    TeacherCheckInDetailSerializer,
)

class IsTeacher(permissions.BasePermission):
    """只允许教师访问的权限"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'teacher'

class IsStudent(permissions.BasePermission):
    """只允许学生访问的权限"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'

class CourseViewSet(viewsets.ModelViewSet):
    """
    课程视图集，提供课程的增删改查功能
    """
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """根据当前用户角色返回不同的查询集"""
        user = self.request.user
        if user.role == 'teacher':
            return Course.objects.filter(teacher=user)
        else:  # 学生
            return Course.objects.filter(students=user)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """获取当前正在进行的课程，包含签到信息"""
        user = request.user
        today_weekday = timezone.now().weekday() + 1  # 1-7代表周一到周日
        now_time = timezone.localtime(timezone.now()).time()
        
        # 筛选今天、当前时间段的课程
        if user.role == 'student':
            courses = Course.objects.filter(
                students=user,
                week_days__contains=str(today_weekday)  # 检查week_days字符串是否包含今天的星期几
            ).filter(
                Q(time_start__lte=now_time, time_end__gte=now_time) |  # 当前时间在课程时间内
                Q(time_start__gte=now_time, time_start__hour=now_time.hour)  # 或即将在本小时内开始
            )
        else:  # 老师
            courses = Course.objects.filter(
                teacher=user,
                week_days__contains=str(today_weekday)
            ).filter(
                Q(time_start__lte=now_time, time_end__gte=now_time) |
                Q(time_start__gte=now_time, time_start__hour=now_time.hour)
            )
        
        serializer = ActiveCourseSerializer(courses, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """获取即将到来的课程"""
        user = request.user
        today_weekday = timezone.now().weekday() + 1
        now_time = timezone.localtime(timezone.now()).time()
        
        # 筛选今天稍后或未来几天的课程
        if user.role == 'student':
            # 今天稍后的课程
            today_courses = Course.objects.filter(
                students=user,
                week_days__contains=str(today_weekday),
                time_start__gt=now_time
            ).exclude(time_start__hour=now_time.hour)  # 排除已在'active'中显示的本小时课程
            
            # 未来几天的课程（最多显示5天）
            future_courses = []
            for day_offset in range(1, 6):  # 从明天开始，最多查找5天
                future_weekday = (today_weekday + day_offset) % 7 or 7  # 避免0，使用1-7表示
                courses = Course.objects.filter(
                    students=user,
                    week_days__contains=str(future_weekday)
                )
                future_courses.extend(list(courses))
                if len(future_courses) >= 5:  # 最多显示5门未来课程
                    break
            
            # 合并并排序
            all_courses = list(today_courses) + future_courses[:5]
        else:  # 教师
            # 类似逻辑处理教师的课程
            today_courses = Course.objects.filter(
                teacher=user,
                week_days__contains=str(today_weekday),
                time_start__gt=now_time
            ).exclude(time_start__hour=now_time.hour)
            
            future_courses = []
            for day_offset in range(1, 6):
                future_weekday = (today_weekday + day_offset) % 7 or 7
                courses = Course.objects.filter(
                    teacher=user,
                    week_days__contains=str(future_weekday)
                )
                future_courses.extend(list(courses))
                if len(future_courses) >= 5:
                    break
            
            all_courses = list(today_courses) + future_courses[:5]
        
        serializer = CourseSerializer(all_courses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsTeacher])
    def teacher(self, request):
        """获取教师的所有课程"""
        courses = Course.objects.filter(teacher=request.user)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)


class CheckInCreateAPIView(generics.CreateAPIView):
    """创建签到活动"""
    serializer_class = CheckInCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        check_in = serializer.save()
        
        # 返回创建成功的签到信息
        return Response({
            'id': check_in.id,
            'course_name': check_in.course.name,
            'check_in_code': check_in.check_in_code,
            'expires_at': check_in.expires_at,
            'message': '签到创建成功'
        }, status=status.HTTP_201_CREATED)


class StudentCheckInAPIView(generics.CreateAPIView):
    """学生签到接口"""
    serializer_class = StudentCheckInSubmitSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        student_check_in = serializer.save()
        
        # 返回签到结果
        return Response({
            'id': student_check_in.id,
            'course_name': student_check_in.check_in.course.name,
            'check_in_time': student_check_in.check_in_time,
            'status': student_check_in.status,
            'message': '签到成功'
        }, status=status.HTTP_201_CREATED)


class CheckInHistoryAPIView(generics.ListAPIView):
    """学生签到历史记录"""
    serializer_class = CheckInHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # 获取学生的签到记录，按时间倒序排列
        if user.role == 'student':
            return StudentCheckIn.objects.filter(student=user).order_by('-check_in_time')
        else:
            # 老师看不到此记录，返回空
            return StudentCheckIn.objects.none()


class CheckInDetailAPIView(generics.RetrieveAPIView):
    """教师查看签到详情"""
    serializer_class = TeacherCheckInDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    
    def get_queryset(self):
        # 只能查看自己创建的签到
        return CheckIn.objects.filter(created_by=self.request.user)


class CheckInStudentsAPIView(generics.ListAPIView):
    """查看某次签到的学生名单"""
    serializer_class = StudentCheckInSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    
    def get_queryset(self):
        check_in_id = self.kwargs.get('check_in_id')
        check_in = get_object_or_404(CheckIn, id=check_in_id, created_by=self.request.user)
        return StudentCheckIn.objects.filter(check_in=check_in).order_by('check_in_time')


class EndCheckInAPIView(generics.GenericAPIView):
    """结束签到活动"""
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    
    def post(self, request, pk):
        # 获取签到活动
        check_in = get_object_or_404(CheckIn, id=pk, created_by=request.user)
        
        # 检查签到是否已经结束
        if check_in.status != 'active':
            return Response(
                {"error": "此签到活动已结束或已取消"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 结束签到
        check_in.status = 'expired'
        check_in.expires_at = timezone.now()
        check_in.save()
        
        # 处理未签到的学生（标记为缺勤）
        enrolled_students = check_in.course.students.all()
        checked_in_students = StudentCheckIn.objects.filter(check_in=check_in).values_list('student_id', flat=True)
        
        # 找出未签到的学生
        absent_students = enrolled_students.exclude(id__in=checked_in_students)
        
        # 创建缺勤记录
        for student in absent_students:
            StudentCheckIn.objects.create(
                check_in=check_in,
                student=student,
                status='absent',
                notes='系统自动标记缺勤'
            )
        
        return Response(
            {
                "message": "签到活动已结束",
                "absent_count": absent_students.count()
            },
            status=status.HTTP_200_OK
        )