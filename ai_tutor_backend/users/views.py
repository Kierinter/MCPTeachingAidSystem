from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token

from django.utils import timezone
from django.contrib.auth import authenticate

from users.models import User
from users.check_in import CheckInRecord
from users.serializers import (
    UserSerializer, UserRegistrationSerializer,
    CheckInSerializer, CheckInCreateSerializer
)

class UserViewSet(viewsets.ModelViewSet):
    """用户视图集，提供用户的CRUD操作"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # 普通用户只能查看自己的信息，管理员可以查看所有用户
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=user.id)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer

class RegisterView(generics.CreateAPIView):
    """用户注册视图"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    """获取当前登录用户信息"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

class CheckInViewSet(viewsets.ModelViewSet):
    """签到记录视图集"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            # 管理员可以查看所有记录
            return CheckInRecord.objects.all().order_by('-check_in_date')
        # 普通用户只能查看自己的记录
        return CheckInRecord.objects.filter(user=user).order_by('-check_in_date')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CheckInCreateSerializer
        return CheckInSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """检查今天是否已签到"""
        today_check_in = CheckInRecord.objects.filter(
            user=request.user, 
            check_in_date=timezone.now().date()
        ).first()
        
        if today_check_in:
            serializer = self.get_serializer(today_check_in)
            return Response(serializer.data)
        else:
            return Response({"detail": "今天还未签到"}, status=status.HTTP_404_NOT_FOUND)

class LoginView(APIView):
    """用户登录视图"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({'error': '请提供用户名和密码'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        
        if not user:
            return Response({'error': '用户名或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)
        
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key
        })

class UserProfileView(APIView):
    """获取用户信息视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)