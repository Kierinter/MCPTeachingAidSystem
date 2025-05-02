from rest_framework import serializers
from .models import Subject, Topic, Problem, UserProblemRecord

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'description']

class TopicSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    
    class Meta:
        model = Topic
        fields = ['id', 'name', 'description', 'subject', 'subject_name']

class ProblemSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    subject_name = serializers.CharField(source='topic.subject.name', read_only=True)
    
    class Meta:
        model = Problem
        fields = ['id', 'topic', 'topic_name', 'subject_name', 'title', 'content', 
                  'difficulty', 'created_at']

class ProblemDetailSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    subject_name = serializers.CharField(source='topic.subject.name', read_only=True)
    
    class Meta:
        model = Problem
        fields = ['id', 'topic', 'topic_name', 'subject_name', 'title', 'content', 
                  'answer', 'explanation', 'difficulty', 'created_at']

class ProblemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = ['topic', 'title', 'content', 'answer', 'explanation', 'difficulty']

class UserProblemRecordSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    
    class Meta:
        model = UserProblemRecord
        fields = ['id', 'problem', 'problem_title', 'user_answer', 'status', 
                  'score', 'time_spent', 'attempted_at']

class UserProblemRecordCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProblemRecord
        fields = ['problem', 'user_answer', 'time_spent']