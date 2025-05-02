from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from django.utils import timezone

from .models import Subject, Topic, Problem, UserProblemRecord
from .serializers import (
    SubjectSerializer, TopicSerializer, 
    ProblemSerializer, ProblemDetailSerializer, ProblemCreateSerializer,
    UserProblemRecordSerializer, UserProblemRecordCreateSerializer
)

class IsTeacherOrReadOnly(permissions.BasePermission):
    """
    教师可以执行所有操作，其他用户只能读取
    """
    def has_permission(self, request, view):
        # 允许所有用户进行GET、HEAD、OPTIONS请求
        if request.method in permissions.SAFE_METHODS:
            return True
        # 仅允许教师进行修改操作
        return request.user and request.user.role == 'teacher'

class SubjectViewSet(viewsets.ModelViewSet):
    """学科视图集"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsTeacherOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class TopicViewSet(viewsets.ModelViewSet):
    """知识点视图集"""
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [IsTeacherOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'subject__name']
    
    def get_queryset(self):
        queryset = Topic.objects.all()
        subject_id = self.request.query_params.get('subject', None)
        
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        
        return queryset

class ProblemViewSet(viewsets.ModelViewSet):
    """题目视图集"""
    queryset = Problem.objects.all()
    permission_classes = [IsTeacherOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'content', 'topic__name', 'topic__subject__name']
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return ProblemCreateSerializer
        elif self.action == 'retrieve':
            return ProblemDetailSerializer
        return ProblemSerializer
    
    def get_queryset(self):
        queryset = Problem.objects.all()
        
        # 过滤条件
        topic_id = self.request.query_params.get('topic', None)
        subject_id = self.request.query_params.get('subject', None)
        difficulty = self.request.query_params.get('difficulty', None)
        
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        
        if subject_id:
            queryset = queryset.filter(topic__subject_id=subject_id)
        
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def user_record(self, request, pk=None):
        """获取当前用户对特定题目的作答记录"""
        try:
            record = UserProblemRecord.objects.get(
                user=request.user,
                problem_id=pk
            )
            serializer = UserProblemRecordSerializer(record)
            return Response(serializer.data)
        except UserProblemRecord.DoesNotExist:
            return Response({"detail": "尚未作答此题"}, status=status.HTTP_404_NOT_FOUND)

class UserProblemRecordViewSet(viewsets.ModelViewSet):
    """用户题目记录视图集"""
    serializer_class = UserProblemRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """只允许用户查看自己的记录，教师可查看所有"""
        user = self.request.user
        if user.role == 'teacher':
            return UserProblemRecord.objects.all()
        return UserProblemRecord.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserProblemRecordCreateSerializer
        return UserProblemRecordSerializer
    
    def perform_create(self, serializer):
        """创建记录时自动评分"""
        problem_id = self.request.data.get('problem')
        user_answer = self.request.data.get('user_answer', '')
        
        try:
            problem = Problem.objects.get(id=problem_id)
            # 简单的完全匹配判题（实际项目中可以用更复杂的判题逻辑）
            correct_answer = problem.answer.strip()
            user_answer = user_answer.strip()
            
            if user_answer == correct_answer:
                status_value = 'correct'
                score = 100
            elif user_answer and len(user_answer) > 0:
                # 这里可以添加部分正确的判断逻辑
                status_value = 'incorrect'
                score = 0
            else:
                status_value = 'skipped'
                score = 0
            
            # 检查是否已有记录，如有则更新
            try:
                existing_record = UserProblemRecord.objects.get(
                    user=self.request.user,
                    problem_id=problem_id
                )
                existing_record.user_answer = user_answer
                existing_record.status = status_value
                existing_record.score = score
                existing_record.time_spent = self.request.data.get('time_spent', 0)
                existing_record.attempted_at = timezone.now()
                existing_record.save()
                return existing_record
            except UserProblemRecord.DoesNotExist:
                # 创建新记录
                serializer.save(
                    user=self.request.user,
                    status=status_value,
                    score=score
                )
                
        except Problem.DoesNotExist:
            raise serializers.ValidationError({"problem": "题目不存在"})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取用户的做题统计信息"""
        user = request.user
        records = UserProblemRecord.objects.filter(user=user)
        
        total_attempted = records.count()
        correct_count = records.filter(status='correct').count()
        incorrect_count = records.filter(status='incorrect').count()
        skipped_count = records.filter(status='skipped').count()
        
        avg_score = records.aggregate(Avg('score'))['score__avg'] or 0
        
        return Response({
            "total_attempted": total_attempted,
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "skipped_count": skipped_count,
            "avg_score": round(avg_score, 2)
        })