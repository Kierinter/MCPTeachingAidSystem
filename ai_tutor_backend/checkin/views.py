from rest_framework import viewsets, generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import CheckIn, StudentCheckIn
from .serializers import (
    CheckInSerializer, 
    CheckInCreateSerializer, 
    StudentCheckInSerializer,
    StudentCheckInSubmitSerializer,
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
            'check_in_code': check_in.check_in_code,
            'expires_at': check_in.expires_at,
            'class_name': check_in.class_name,
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
    lookup_field = 'pk'  # 显式指定主键字段

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
        checked_in_students = StudentCheckIn.objects.filter(check_in=check_in).values_list('student_id', flat=True)
        
        # 找出未签到的学生
        absent_students = check_in.course.students.exclude(id__in=checked_in_students)
        
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

class ActiveCheckInsAPIView(generics.ListAPIView):
    """获取当前活动的签到"""
    serializer_class = CheckInSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        now = timezone.now()
        # 获取当前有效的签到活动
        return CheckIn.objects.filter(
            status='active',
            expires_at__gt=now
        ).order_by('-created_at')