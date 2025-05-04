from django.urls import path
from .views import (
    CheckInCreateAPIView,
    StudentCheckInAPIView,
    CheckInHistoryAPIView,
    CheckInDetailAPIView,
    CheckInStudentsAPIView,
    EndCheckInAPIView,
)

urlpatterns = [
    path('checkin/create/', CheckInCreateAPIView.as_view(), name='create-checkin'),
    path('checkin/submit/', StudentCheckInAPIView.as_view(), name='submit-checkin'),
    path('checkin/history/', CheckInHistoryAPIView.as_view(), name='checkin-history'),
    path('checkin/<int:pk>/', CheckInDetailAPIView.as_view(), name='checkin-detail'),
    path('checkin/<int:check_in_id>/students/', CheckInStudentsAPIView.as_view(), name='checkin-students'),
    path('checkin/end/<int:pk>/', EndCheckInAPIView.as_view(), name='end-checkin'),
]