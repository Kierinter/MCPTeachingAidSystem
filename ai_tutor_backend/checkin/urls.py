from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CourseViewSet,
    CheckInCreateAPIView,
    StudentCheckInAPIView,
    CheckInHistoryAPIView,
    CheckInDetailAPIView,
    CheckInStudentsAPIView,
    EndCheckInAPIView,
)

# 创建路由器，并注册课程视图集
router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')

# URL模式
urlpatterns = [
    # 包含路由器生成的URL
    path('', include(router.urls)),
    
    # 课程相关接口
    path('courses/active/', CourseViewSet.as_view({'get': 'active'}), name='active-courses'),
    path('courses/upcoming/', CourseViewSet.as_view({'get': 'upcoming'}), name='upcoming-courses'),
    path('courses/teacher/', CourseViewSet.as_view({'get': 'teacher'}), name='teacher-courses'),
    
    # 签到相关接口
    path('courses/check-in/create/', CheckInCreateAPIView.as_view(), name='create-checkin'),
    path('courses/check-in/submit/', StudentCheckInAPIView.as_view(), name='submit-checkin'),
    path('courses/check-in/history/', CheckInHistoryAPIView.as_view(), name='checkin-history'),
    path('courses/check-in/<int:pk>/', CheckInDetailAPIView.as_view(), name='checkin-detail'),
    path('courses/check-in/<int:check_in_id>/students/', CheckInStudentsAPIView.as_view(), name='checkin-students'),
    path('courses/check-in/<int:pk>/end/', EndCheckInAPIView.as_view(), name='end-checkin'),
]