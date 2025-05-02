from rest_framework import serializers
from django.utils import timezone
from users.models import User
from users.check_in import CheckInRecord

class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    class Meta:
        model = User
        fields = ('id', 'username', 'real_name', 'role', 'email')
        read_only_fields = ('id',)

class UserRegistrationSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'real_name', 'role', 'email', 'password', 'password2')
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({"password": "两次输入的密码不一致"})
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            real_name=validated_data['real_name'],
            role=validated_data['role'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

class CheckInSerializer(serializers.ModelSerializer):
    """签到记录序列化器"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = CheckInRecord
        fields = ('id', 'user', 'check_in_date', 'check_in_time')
        read_only_fields = ('id', 'user', 'check_in_date', 'check_in_time')

class CheckInCreateSerializer(serializers.ModelSerializer):
    """创建签到记录序列化器"""
    class Meta:
        model = CheckInRecord
        fields = ('notes',)
        
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        
        # 检查今天是否已签到
        today_check_in = CheckInRecord.objects.filter(
            user=user, 
            check_in_date=timezone.now().date()
        ).first()
        
        if today_check_in:
            raise serializers.ValidationError({"detail": "今天已经签到过了"})
            
        # 获取客户端IP
        x_forwarded_for = self.context['request'].META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            validated_data['check_in_ip'] = x_forwarded_for.split(',')[0]
        else:
            validated_data['check_in_ip'] = self.context['request'].META.get('REMOTE_ADDR')
            
        return super().create(validated_data)