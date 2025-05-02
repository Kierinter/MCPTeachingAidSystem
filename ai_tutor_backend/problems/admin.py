from django.contrib import admin
from .models import Subject, Topic, Problem, UserProblemRecord

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'description')
    search_fields = ('name', 'subject__name')
    list_filter = ('subject',)

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'difficulty', 'created_at')
    list_filter = ('topic__subject', 'topic', 'difficulty')
    search_fields = ('title', 'content')

@admin.register(UserProblemRecord)
class UserProblemRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'problem', 'status', 'score', 'attempted_at')
    list_filter = ('status', 'score', 'attempted_at')
    search_fields = ('user__username', 'problem__title')
    raw_id_fields = ('user', 'problem')