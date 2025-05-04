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
    weak_subjects_list = serializers.SerializerMethodField()
    real_name = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentProfile
        fields = ['id', 'student', 'student_name', 'student_number', 'addmisson_year', 'grade',
                  'class_name', 'academic_level', 'weak_subjects', 'weak_subjects_list', 'notes',
                  'created_at', 'updated_at', 'real_name']
        read_only_fields = ['id', 'student', 'created_at', 'updated_at']
    
    def get_student_name(self, obj):
        # 优先 real_name，没有则用 username
        if not obj.student:
            return ''
        if hasattr(obj.student, 'real_name') and obj.student.real_name:
            return obj.student.real_name
        return obj.student.username if obj.student else ''
    
    def get_weak_subjects_list(self, obj):
        """获取薄弱学科列表"""
        return obj.get_weak_subjects_list()
    
    def get_real_name(self, obj):
        """获取真实姓名"""
        if not obj.student:
            return ''
        if hasattr(obj.student, 'real_name'):
            return obj.student.real_name
        return ''


class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    """学生档案更新序列化器"""
    class Meta:
        model = StudentProfile
        fields = ['grade', 'class_name', 'academic_level', 'weak_subjects', 'notes']


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
        if not obj.student:
            return ''
        if hasattr(obj.student, 'real_name') and obj.student.real_name:
            return obj.student.real_name
        return obj.student.username if obj.student else ''