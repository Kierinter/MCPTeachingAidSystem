from rest_framework import viewsets, generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import StudentProfile, AcademicRecord
from .serializers import (
    StudentProfileSerializer,
    StudentProfileUpdateSerializer,
    AcademicRecordSerializer
)
from checkin.views import IsTeacher

User = get_user_model()


class StudentProfileViewSet(viewsets.ModelViewSet):
    """学生档案视图集"""
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    
    def get_queryset(self):
        """返回所有学生档案，"""
        return StudentProfile.objects.all().order_by('student_number')
    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        student_name = data.get('student_name')
        student_number = data.get('student_number')
        # 检查学号是否已存在
        if StudentProfile.objects.filter(student_number=student_number).exists():
            return Response({'detail': '学号已存在'}, status=status.HTTP_400_BAD_REQUEST)
        # 自动创建用户
        user = User.objects.create_user(
            username=student_number,
            real_name=student_name,
            role='student',
            is_active=True
        )
        user.set_password('123456')
        user.save()
        # 创建学生档案
        profile = StudentProfile.objects.create(
            student=user,
            student_number=student_number,
            grade=data.get('grade', ''),
            major=data.get('major', ''),
            class_name=data.get('class_name', ''),
            academic_level=data.get('academic_level', 'average'),
            weak_subjects=data.get('weak_subjects', ''),
            notes=data.get('notes', '')
        )
        serializer = self.get_serializer(profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        # 允许修改档案基本信息
        for field in ['student_number', 'grade', 'major', 'class_name', 'academic_level', 'weak_subjects', 'notes']:
            if field in data:
                setattr(instance, field, data[field])
        instance.save()
        # 同步修改用户姓名
        if 'student_name' in data:
            instance.student.real_name = data['student_name']
            instance.student.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_profile(self, request, pk=None):
        """更新学生档案"""
        profile = self.get_object()
        serializer = StudentProfileUpdateSerializer(
            profile, data=request.data, partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': '学生档案已更新',
                'data': StudentProfileSerializer(profile).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AcademicRecordViewSet(viewsets.ModelViewSet):
    """学生学习记录视图集"""
    serializer_class = AcademicRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    
    def get_queryset(self):
        """获取教师有权限访问的学生学习记录"""
        user = self.request.user
        if user.role != 'teacher':
            return AcademicRecord.objects.none()
        
        # 获取教师教授的所有课程的学生的学习记录
        return AcademicRecord.objects.filter(
            student__enrolled_courses__teacher=user
        ).order_by('-exam_date')
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        """获取指定学生的学习记录"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {"error": "必须提供学生ID参数"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 确认教师有权限访问该学生
        student = get_object_or_404(User, id=student_id)
        if not student.enrolled_courses.filter(teacher=request.user).exists():
            return Response(
                {"error": "您没有权限访问此学生的信息"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        records = AcademicRecord.objects.filter(student=student).order_by('-exam_date')
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        """创建学习记录时验证权限"""
        student_id = self.request.data.get('student')
        student = get_object_or_404(User, id=student_id)
        
        # 确认教师有权限为该学生创建记录
        if not student.enrolled_courses.filter(teacher=self.request.user).exists():
            raise permissions.PermissionDenied("您没有权限为此学生创建记录")
        
        serializer.save(student=student)