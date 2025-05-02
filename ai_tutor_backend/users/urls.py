from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('users', views.UserViewSet)
router.register('checkin', views.CheckInViewSet, basename='checkin')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('me/', views.current_user, name='current_user'),
    path('checkin/today/', views.CheckInViewSet.as_view({'get': 'today'}), name='today_checkin'),
]