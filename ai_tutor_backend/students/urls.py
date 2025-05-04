from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    StudentProfileViewSet,
    AcademicRecordViewSet,
)

# 创建路由器，并注册视图集
router = DefaultRouter()
router.register(r'profiles', StudentProfileViewSet, basename='student-profile')
router.register(r'records', AcademicRecordViewSet, basename='academic-record')

# URL模式
urlpatterns = [
    # 包含路由器生成的URL
    path('', include(router.urls)),
]