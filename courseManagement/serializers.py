from rest_framework import serializers
from .models import CourseSchedule, AttendanceRecord, AttendanceSession, StudentCourseCard



class CourseScheduleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CourseSchedule
        fields = [ 'id', 'course_title', 'course_code', 'course_location', 'day', 'geofencing', 'is_elective', 'department', 'attendance_rate', 'start_time', 'end_time', 'schedule_status', 'level', 'number_of_students']



class CourseListSerializer(serializers.ModelSerializer):

    class Meta:
        model = CourseSchedule
        fields = ['course_code']


class AttendanceRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = AttendanceRecord
        fields = ['first_name', 'last_name', 'matric_number', 'level', 'course_code', 'status', 'method', 'time']


class AttendanceSessionSerializer(serializers.ModelSerializer):

    qr_image = serializers.ImageField(use_url=True)

    class Meta:
        model = AttendanceSession
        fields = ['session_id', 'course_title', 'course_code', 'course_location', 'start_time', 'level', 'end_time', 'token',
                   'qr_image', 'geofencing', 'schedule_status', 'total_student', 'present', 'absent', 'expires_at', 'attendance_rate']
        

class AttendanceHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = AttendanceRecord
        fields = ['course_title', 'status', 'time', 'date']


class StudentCourseCardSerializer(serializers.ModelSerializer):

    class Meta:
        model = StudentCourseCard
        fields = ['email', 'first_name', 'last_name', 'matric_number', 'level', 'course_code', 'attendance_percentage', 'eligible_for_exam', 'attendance_score', 'department']