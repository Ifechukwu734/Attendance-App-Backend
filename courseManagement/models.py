from django.db import models
from django.conf import settings

# Create your models here.

DEPARTMENT = (
        ('Computer Science', 'Computer Science'),
        ('Mathematics', 'Mathematics'),
        ('Statistics', 'Statistics'),
        ('Physics', 'Physics'),
        ('Chemistry', 'Chemistry'),
        ('Geology', 'Geology')
    )


class CourseSchedule(models.Model):

    SCHEDULE_STATUS = (
        ('In Progress', 'In Progress'),
        ('Upcoming', 'Upcoming'),
        ('Ended', 'Ended')
    )

    course_title = models.CharField(max_length=225)
    course_code = models.CharField(max_length=20, default='')
    course_location = models.CharField(max_length=225)
    day = models.CharField(max_length=225)
    start_time = models.TimeField()
    end_time = models.TimeField()
    department = models.CharField(max_length=225, choices=DEPARTMENT)
    schedule_status = models.CharField(max_length=50, choices=SCHEDULE_STATUS, default='Upcoming')
    level = models.CharField(max_length=20, default='')
    number_of_students = models.IntegerField(default=0)
    is_elective = models.BooleanField(default=False)
    attendance_rate = models.FloatField(default=0)
    geofencing = models.IntegerField(default=0)
    lecturer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.course_title
    



class AttendanceSession(models.Model):
    SCHEDULE_STATUS = (
        ('Session Active', 'Session Active'),
        ('Session Ended', 'Session Ended')
    )
    session_id = models.CharField(max_length=12)
    course_title = models.CharField(max_length=225)
    course_code = models.CharField(max_length=20, default='')
    course_location = models.CharField(max_length=225)
    level = models.CharField(max_length=12)
    start_time = models.TimeField()
    course = models.ForeignKey(CourseSchedule, on_delete=models.CASCADE)
    end_time = models.TimeField()
    longitude = models.FloatField()
    lattitude = models.FloatField()
    token = models.CharField(max_length=6)
    qr_image = models.ImageField(upload_to='qr-code/')
    geofencing = models.IntegerField(default=0)
    lecturer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    schedule_status = models.CharField(max_length=50, choices=SCHEDULE_STATUS, default='Session Active')
    ended_session = models.BooleanField(default=False)
    total_student = models.IntegerField()
    present = models.IntegerField()
    absent = models.IntegerField()
    expires_at = models.DateTimeField(null=True)
    attendance_rate = models.IntegerField()



class AttendanceRecord(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_attendance_record')
    first_name = models.CharField(max_length=225)
    last_name = models.CharField(max_length=225)
    matric_number = models.CharField(max_length=20)
    level = models.CharField(max_length=12)
    session = models.ForeignKey(AttendanceSession, on_delete=models.SET_NULL, null=True)
    department = models.CharField(max_length=225, choices=DEPARTMENT)
    course = models.ForeignKey(CourseSchedule, on_delete=models.CASCADE)
    course_code = models.CharField(max_length=20)
    course_title = models.CharField(max_length=225, default='Database Design')
    status = models.CharField(max_length=20)
    method = models.CharField(max_length=30)
    time = models.TimeField()
    date = models.DateTimeField(auto_now_add=True)
    lecturer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)



class StudentCourseCard(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_course_card')
    course = models.ForeignKey(CourseSchedule, on_delete=models.CASCADE, null=True)
    course_code = models.CharField(max_length=20)
    email = models.EmailField()
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    matric_number = models.CharField(max_length=20, default='')
    level = models.CharField(max_length=12, default='', blank=True, null=True)
    department = models.CharField(max_length=225, choices=DEPARTMENT, default='')
    eligible_for_exam = models.BooleanField(default=False)
    attendance_score = models.IntegerField()
    attendance_percentage = models.IntegerField(default=0)
    lecturer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)