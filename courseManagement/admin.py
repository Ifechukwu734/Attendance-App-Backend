from django.contrib import admin
from .models import CourseSchedule, AttendanceSession, AttendanceRecord, StudentCourseCard
# Register your models here.


admin.site.register(CourseSchedule)

admin.site.register(AttendanceSession)

admin.site.register(AttendanceRecord)

admin.site.register(StudentCourseCard)