from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json


class DisplayLiveAttendanceRecord(WebsocketConsumer):

    def connect(self):
        self.room_group_name = self.scope['url_route']['kwargs']['session_id']
        self.user = 'Anonymous User'
        print(type(self.room_group_name), self.room_group_name)
        print("Consumer group:", self.room_group_name)
        print("Joining group:", self.room_group_name)
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        print("Channel:", self.channel_name)
        self.accept()

    
    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    
    def display_live_attendance(self, event):
        print("EVENT RECEIVED:", event)
        from .models import AttendanceSession, AttendanceRecord
        from .serializers import AttendanceRecordSerializer
        session_id = event['session_id']
        session = AttendanceSession.objects.filter(session_id=session_id).first()
        attendance_records = AttendanceRecord.objects.filter(session=session).order_by('-date')
        serializer = AttendanceRecordSerializer(attendance_records, many=True)
        content = serializer.data
        print(serializer.data)

        self.send(
            text_data = json.dumps({'message': content})
        )