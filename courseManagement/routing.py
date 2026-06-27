from django.urls import path
from .consumers import DisplayLiveAttendanceRecord

websocket_urlpatterns = [
    path('ws/live-attendance/<session_id>', DisplayLiveAttendanceRecord.as_asgi())
]