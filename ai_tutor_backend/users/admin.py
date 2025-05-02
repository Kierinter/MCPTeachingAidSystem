from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from .check_in import CheckInRecord

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """用户管理界面"""
    list_display = ('username', 'real_name', 'role', 'email', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'real_name', 'email')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('个人信息', {'fields': ('real_name', 'role')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('个人信息', {'fields': ('real_name', 'role')}),
    )

@admin.register(CheckInRecord)
class CheckInRecordAdmin(admin.ModelAdmin):
    """签到记录管理界面"""
    list_display = ('user', 'check_in_date', 'check_in_time', 'check_in_ip')
    list_filter = ('check_in_date',)
    search_fields = ('user__username', 'user__real_name')
    date_hierarchy = 'check_in_date'