from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('subjects', views.SubjectViewSet)
router.register('topics', views.TopicViewSet)
router.register('problems', views.ProblemViewSet)
router.register('records', views.UserProblemRecordViewSet, basename='records')

urlpatterns = [
    path('', include(router.urls)),
]