from rest_framework import viewsets, permissions, status, filters
from rest_framework import serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from django.utils import timezone
from students.models import StudentProfile
import random
import os
import json
import time
from openai import OpenAI
from rest_framework.permissions import IsAuthenticated

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
        subject_id = self.request.query_params.get('subject_id', None)
        subject_name = self.request.query_params.get('subject', None)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        elif subject_name:
            queryset = queryset.filter(subject__name=subject_name)
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

    @action(detail=False, methods=['get'])
    def recommend(self, request):
        """根据学生档案推荐10道题目"""
        user = request.user
        try:
            profile = StudentProfile.objects.get(student=user)
        except StudentProfile.DoesNotExist:
            return Response({'detail': '未找到学生档案'}, status=status.HTTP_404_NOT_FOUND)
        # 获取薄弱学科和学业水平
        weak_subjects = profile.get_weak_subjects_list()
        academic_level = profile.academic_level
        # 学业水平与题目难度的映射
        level_map = {
            'excellent': '困难',
            'good': '较难',
            'average': '中等',
            'below_average': '简单',
            'poor': '简单',
        }
        difficulty = level_map.get(academic_level, None)
        # 先从薄弱学科中抽题
        problems = Problem.objects.all()
        if weak_subjects:
            problems = problems.filter(topic__subject__name__in=weak_subjects)
        if difficulty:
            problems = problems.filter(difficulty=difficulty)
        problems = list(problems)
        # 随机抽取10道题
        if len(problems) > 10:
            problems = random.sample(problems, 10)
        serializer = ProblemSerializer(problems, many=True)
        return Response(serializer.data)

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

    @action(detail=False, methods=['get'])
    def wrongbook(self, request):
        """获取当前用户的错题本（错误和部分正确的题目）"""
        user = request.user
        records = UserProblemRecord.objects.filter(
            user=user,
            status__in=['incorrect', 'partially_correct']
        ).order_by('-attempted_at')
        # 题目信息+作答信息
        data = []
        for rec in records:
            problem = rec.problem
            data.append({
                'record_id': rec.id,
                'problem_id': problem.id,
                'title': problem.title,
                'content': problem.content,
                'topic_name': problem.topic.name,
                'subject_name': problem.topic.subject.name,
                'difficulty': problem.difficulty,
                'user_answer': rec.user_answer,
                'status': rec.status,
                'score': rec.score,
                'attempted_at': rec.attempted_at,
                'answer': problem.answer,
                'explanation': problem.explanation,
            })
        return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_generate_problems(request):
    """
    AI生成题目接口：根据科目、难度、主题、数量生成题目和解析
    POST参数: subject, topic, difficulty, count
    """
    user = request.user
    if not hasattr(user, 'role') or user.role != 'teacher':
        return Response({'detail': '仅教师可用'}, status=status.HTTP_403_FORBIDDEN)
    subject = request.data.get('subject')
    topic = request.data.get('topic')
    difficulty = request.data.get('difficulty')
    count = int(request.data.get('count', 1))
    if not (subject and topic and difficulty and count):
        return Response({'detail': '参数不完整'}, status=status.HTTP_400_BAD_REQUEST)

    # 读取API KEY和base_url
    DEEPSEEK_API_KEY = "sk-53430f09089a436dba84954547afd5fe"
    if not DEEPSEEK_API_KEY:
        return Response({'detail': '未配置DEEPSEEK_API_KEY'}, status=500)
    deepseek = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    problems = []
    generated_problem_hashes = set()  # 用于存储已生成题目的哈希值
    
    for i in range(count):
        # 添加随机性因素，避免生成相似题目
        current_time = str(time.time())
        random_seed = random.randint(1000, 9999)
        
        prompt = f"""请生成一道{subject}题目，满足以下要求：
1. 知识点: {topic}
2. 难度级别: {difficulty}
3. 题目要有明确的题干、答案和解析
4. 请确保题目具有独特性和多样性
5. 基于随机种子{random_seed}生成不同风格的题目
6. 输出格式如下(不要出现反斜杠转义问题)：
{{
    "题目": "(具体题目描述)",
    "知识点": "{topic}",
    "难度": "{difficulty}",
    "答案": "(答案内容)",
    "解析": "(详细解析步骤)"
}}
请确保输出是有效的JSON格式，特别注意：当需要在JSON字符串中包含反斜杠或引号时，请确保正确转义。"""
        
        try:
            response = deepseek.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=1.2 + (i * 0.1),  # 逐渐增加随机性
                max_tokens=1500
            )
            result = response.choices[0].message.content
            print(f"AI回复原始内容: {result}")
            
            # 查找JSON字符串
            start_idx = result.find('{')
            end_idx = result.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                json_str = result[start_idx:end_idx]
                
                # 尝试解析JSON，如果失败，尝试修复常见问题
                try:
                    problem_data = json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {str(e)}")
                    
                    # 尝试替换可能导致问题的转义序列
                    fixed_json = json_str.replace("\\", "\\\\")  # 双重转义反斜杠
                    # 但不要双重转义已经正确转义的引号
                    fixed_json = fixed_json.replace("\\\\\"", "\\\"")
                    
                    try:
                        problem_data = json.loads(fixed_json)
                    except json.JSONDecodeError:
                        # 如果还是失败，返回错误信息
                        problems.append({'error': f'JSON解析错误: {str(e)}'})
                        continue
                
                # 验证所需字段是否存在
                required_fields = ['题目', '知识点', '难度', '答案', '解析']
                if all(field in problem_data for field in required_fields):
                    # 检查题目是否重复
                    problem_hash = hash(problem_data['题目'])
                    if problem_hash in generated_problem_hashes:
                        print("检测到重复题目，重新生成...")
                        continue  # 跳过这次循环，重新生成
                    
                    # 如果不重复，添加到已生成集合和结果列表
                    generated_problem_hashes.add(problem_hash)
                    problems.append(problem_data)
                else:
                    missing = [f for f in required_fields if f not in problem_data]
                    problems.append({
                        'error': f'生成的数据缺少必要字段: {", ".join(missing)}',
                        'data': problem_data
                    })
            else:
                problems.append({'error': 'AI输出格式异常，无法提取JSON'})
                
            # 如果未生成足够数量的题目，可能需要额外尝试几次
            if len(problems) < count and i == count - 1:
                # 最后一次循环但还没生成够题目，继续尝试
                i -= 1
                
        except Exception as e:
            print(f"生成题目错误: {str(e)}")
            problems.append({'error': str(e)})
        time.sleep(0.5)
    
    return Response({'problems': problems})