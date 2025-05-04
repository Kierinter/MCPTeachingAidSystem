from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import StudentProfile, AcademicRecord

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """用户基础信息序列化器"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        read_only_fields = ['id', 'username', 'email', 'role']


class StudentProfileSerializer(serializers.ModelSerializer):
    """学生档案序列化器"""
    student = UserBasicSerializer(read_only=True)
    student_name = serializers.SerializerMethodField()
    academic_level_display = serializers.SerializerMethodField()
    weak_subjects_list = serializers.SerializerMethodField()
    real_name = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentProfile
        fields = ['id', 'student', 'student_name', 'student_number', 'grade', 'major', 
                  'class_name', 'academic_level', 'academic_level_display', 
                  'weak_subjects', 'weak_subjects_list', 'notes', 
                  'created_at', 'updated_at', 'real_name']
        read_only_fields = ['id', 'student', 'created_at', 'updated_at']
    
    def get_student_name(self, obj):
        """获取学生姓名"""
        if obj.student.first_name or obj.student.last_name:
            return f"{obj.student.last_name}{obj.student.first_name}"
        return obj.student.username
    
    def get_academic_level_display(self, obj):
        """获取学业水平显示值"""
        return obj.get_academic_level_display()
    
    def get_weak_subjects_list(self, obj):
        """获取薄弱学科列表"""
        return obj.get_weak_subjects_list()
    
    def get_real_name(self, obj):
        """获取真实姓名"""
        return obj.student.real_name if obj.student else ''


class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    """学生档案更新序列化器"""
    class Meta:
        model = StudentProfile
        fields = ['grade', 'major', 'class_name', 'academic_level', 
                  'weak_subjects', 'notes']


class AcademicRecordSerializer(serializers.ModelSerializer):
    """学生学习记录序列化器"""
    student_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AcademicRecord
        fields = ['id', 'student', 'student_name', 'subject', 'score',
                  'semester', 'exam_type', 'exam_date', 'remarks']
        read_only_fields = ['id', 'student']
    
    def get_student_name(self, obj):
        """获取学生姓名"""
        if obj.student.first_name or obj.student.last_name:
            return f"{obj.student.last_name}{obj.student.first_name}"
        return obj.student.username