from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .serializers import CourseScheduleSerializer, CourseListSerializer, AttendanceSessionSerializer,AttendanceRecordSerializer, AttendanceHistorySerializer
from .models import CourseSchedule, AttendanceRecord, AttendanceSession, StudentCourseCard
from datetime import datetime
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.db.models import Q
from io import BytesIO
from django.core.files.base import ContentFile
from geopy.distance import geodesic
import qrcode
import uuid
import ast
# Create your views here.


# Course Schedule Page for the student App
class CourseScheduleView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user.is_staff:
            today = datetime.now()
            day_name = today.strftime('%A')
            course_schedule = CourseSchedule.objects.filter(department=user.department, day=day_name, level=user.level)
            if course_schedule:
                for course in course_schedule:
                    if course.start_time > timezone.localtime().time():
                        course.schedule_status = 'Upcoming'
                        course.save()
                serializer = CourseScheduleSerializer(course_schedule, many=True)
                data = {
                    'data': serializer.data
                }
                return Response(data, status=status.HTTP_200_OK)
            else:
                data = {
                    'data': 'no class scheduled for today'
                }
                return Response(data, status=status.HTTP_404_NOT_FOUND)
        else:
            data = {
                'data': 'only students can access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        
    

# Recent Course Schedule for Student Dashboard
class PresentCourseView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now =  timezone.localtime(timezone.now())
        user = request.user
        if not user.is_staff:
            today = datetime.now()
            day_name = today.strftime('%A')
            today_date = timezone.localdate()
            print(today_date)
            course_schedule = CourseSchedule.objects.filter(department=user.department, day=day_name, level=user.level)
            present_course = course_schedule.filter(start_time__lte = now, end_time__gte=now, schedule_status='In Progress').first()
            if present_course:
                at = AttendanceRecord.objects.filter(student=user, course=present_course).first()
                
                attendance_record = AttendanceRecord.objects.filter(student=user, date__date=today_date, course=present_course).first()
                serializer = CourseScheduleSerializer(present_course)
                if attendance_record:
                    attendance_serializer = AttendanceRecordSerializer(attendance_record)
                    data = {
                        'data': serializer.data,
                        'attendance': attendance_serializer.data
                    }
                    return Response(data, status=status.HTTP_200_OK)
                else:
                    data = {
                        'data': serializer.data,
                        'attendance': 'Not checked-in yet'
                    }
                    return Response(data, status=status.HTTP_200_OK)
            else:
                attendance_record = AttendanceRecord.objects.filter(student=user, date__date=today_date).last()
                if attendance_record:
                    attendance_serializer = AttendanceRecordSerializer(attendance_record)
                    data = {
                        'data': 'Free period',
                        'attendance': attendance_serializer.data
                    }
                    return Response(data, status=status.HTTP_404_NOT_FOUND)
                else:
                    data = {
                        'data': 'Free Period',
                        'attendance': 'Not checked-in today'
                    }
                    return Response(data, status=status.HTTP_404_NOT_FOUND)
        else:
            data = {
                'data': 'only students can access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)


# List of 3 courses for lecturer's dashboard
class LecturerCoursesView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_staff:
            courses = CourseSchedule.objects.filter(lecturer=user)[:3]
            serializer = CourseScheduleSerializer(courses, many=True)
            data = {
                'data': serializer.data
            }
            return Response(data, status=status.HTTP_200_OK)

        else:
            data = {
                'message': 'you are not authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        



# Lecturer Course Page
class LecturerCoursesManagementView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        User = get_user_model()
        search = request.query_params.get('search')
        level = request.query_params.get('level')
        active_session = 0
        if user.is_staff:
            if search and level:
                if level == 'All Levels':
                    courses = CourseSchedule.objects.filter(Q(lecturer=user, course_title__icontains=search) | Q(lecturer=user, course_code__icontains=search)).order_by('course_title')
                else:
                    courses = CourseSchedule.objects.filter(Q(lecturer=user, course_title__icontains=search, level=level) | Q(lecturer=user, course_code__icontains=search, level=level)).order_by('course_title')
                number_of_courses = courses.count()
                serializer = CourseScheduleSerializer(courses, many=True)
                total_number_of_students = 0
                for course in courses:
                    students = course.number_of_students
                    total_number_of_students += students
                if total_number_of_students > 0:
                    active_session = AttendanceSession.objects.filter(lecturer=user, schedule_status='Session Active').count()
                    total_attendance = AttendanceRecord.objects.filter(lecturer=user).count()
                    total_attendance_result = (total_attendance / total_number_of_students) * 100
                    total_attendance_percentage = round(total_attendance_result)
                    data = {
                        'active_session': active_session,
                        'total_students': total_number_of_students,
                        'number_of_courses': number_of_courses,
                        'average_attendance': total_attendance_percentage,
                        'data': serializer.data
                    }
                    return Response(data, status=status.HTTP_200_OK)
                else:
                    data = {
                        'active_session': active_session,
                        'total_students': 0,
                        'number_of_courses': number_of_courses,
                        'average_attendance': 0,
                        'data': serializer.data
                    }
                    return Response(data, status=status.HTTP_200_OK)
            elif search:
                courses = CourseSchedule.objects.filter(Q(lecturer=user, course_title__icontains=search) | Q(lecturer=user, course_code__icontains=search)).order_by('course_title')
                number_of_courses = courses.count()
                serializer = CourseScheduleSerializer(courses, many=True)
                total_number_of_students = 0
                for course in courses:
                    students = course.number_of_students
                    total_number_of_students += students
                if total_number_of_students > 0:
                    active_session = AttendanceSession.objects.filter(lecturer=user, schedule_status='Session Active').count()
                    total_attendance = AttendanceRecord.objects.filter(lecturer=user).count()
                    total_attendance_result = (total_attendance / total_number_of_students) * 100
                    total_attendance_percentage = round(total_attendance_result)
                    data = {
                        'active_session': active_session,
                        'total_students': total_number_of_students,
                        'number_of_courses': number_of_courses,
                        'average_attendance': total_attendance_percentage,
                        'data': serializer.data
                    }
                    return Response(data, status=status.HTTP_200_OK)
                else:
                    data = {
                        'active_session': active_session,
                        'total_students': 0,
                        'number_of_courses': number_of_courses,
                        'average_attendance': 0,
                        'data': serializer.data
                    }
                    return Response(data, status=status.HTTP_200_OK)    
            elif level:
                if level == 'All Levels':
                    courses = CourseSchedule.objects.filter(lecturer=user).order_by('course_title')
                else:
                    courses = CourseSchedule.objects.filter(lecturer=user, level=level).order_by('course_title')
                number_of_courses = courses.count()
                serializer = CourseScheduleSerializer(courses, many=True)
                total_number_of_students = 0
                for course in courses:
                    students = course.number_of_students
                    total_number_of_students += students
                if total_number_of_students > 0:
                    active_session = AttendanceSession.objects.filter(lecturer=user, schedule_status='Session Active').count()
                    total_attendance = AttendanceRecord.objects.filter(lecturer=user).count()
                    total_attendance_result = (total_attendance / total_number_of_students) * 100
                    total_attendance_percentage = round(total_attendance_result)
                    data = {
                        'active_session': active_session,
                        'total_students': total_number_of_students,
                        'number_of_courses': number_of_courses,
                        'average_attendance': total_attendance_percentage,
                        'data': serializer.data
                    }
                    return Response(data, status=status.HTTP_200_OK)
                else:
                    data = {
                        'active_session': active_session,
                        'total_students': 0,
                        'number_of_courses': number_of_courses,
                        'average_attendance': 0,
                        'data': serializer.data
                    }
                    return Response(data, status=status.HTTP_200_OK)   

            courses = CourseSchedule.objects.filter(lecturer=user).order_by('course_title')
            number_of_courses = courses.count()
            serializer = CourseScheduleSerializer(courses, many=True)
            total_number_of_students = 0
            for course in courses:
                students = course.number_of_students
                total_number_of_students += students
            if total_number_of_students > 0:
                active_session = AttendanceSession.objects.filter(lecturer=user, schedule_status='Session Active').count()
                total_attendance = AttendanceRecord.objects.filter(lecturer=user).count()
                total_attendance_result = (total_attendance / total_number_of_students) * 100
                total_attendance_percentage = round(total_attendance_result)
                data = {
                    'active_session': active_session,
                    'total_students': total_number_of_students,
                    'number_of_courses': number_of_courses,
                    'average_attendance': total_attendance_percentage,
                    'data': serializer.data
                }
                return Response(data, status=status.HTTP_200_OK)
            else:
                data = {
                    'active_session': active_session,
                    'total_students': 0,
                    'number_of_courses': number_of_courses,
                    'average_attendance': 0,
                    'data': serializer.data
                }
                return Response(data, status=status.HTTP_200_OK)

        else:
            data = {
                'message': 'you are not authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        
    # Adding a course by the lecturer
    def post(self, request):
        user = request.user
        number_of_students = request.data.get('number_of_students')
        course_title = request.data.get('course_title')
        course_code = request.data.get('course_code')
        course_location = request.data.get('course_location')
        level = request.data.get('level')
        day = request.data.get('day')
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')
        is_elective = request.data.get('is_elective')
        geo_fencing = request.data.get('geo_fencing')
        department = request.data.get('department')
        if user.is_staff:
            if CourseSchedule.objects.filter(course_code=course_code).exists():
                data = {
                    'message': 'course already exists'
                }
                return Response(data, status=status.HTTP_302_FOUND)
            User = get_user_model()
            course_schedule = CourseSchedule.objects.create(course_title=course_title, course_code=course_code, course_location=course_location, day=day, department=department,
                                                            level=level,  is_elective=is_elective, start_time=start_time, end_time=end_time,
                                                            geofencing=geo_fencing, lecturer=user)
            if course_schedule.is_elective == True:
                course_schedule.number_of_students = int(number_of_students)
                course_schedule.save()
            else:
                students = User.objects.filter(department=course_schedule.department, level=course_schedule.level, is_staff=False).count()
                course_schedule.number_of_students = students
                course_schedule.save()
            data = {
                'message': 'Course added successfully'
            }
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            data = {
                'message': 'you are not authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        

    # update course in course page
    def patch(self, request):
        user = request.user
        if user.is_staff:
            course_id = request.data.get('course_id')
            course_title = request.data.get('course_title')
            course_code = request.data.get('course_code')
            course_location = request.data.get('course_location')
            level = request.data.get('level')
            day = request.data.get('day')
            start_time = request.data.get('start_time')
            end_time = request.data.get('end_time')
            department = request.data.get('department')
            is_elective = request.data.get('is_elective')
            geo_fencing = request.data.get('geo_fencing')
            number_of_students = request.data.get('number_of_students')
            schedule_status = request.data.get('schedule_status')
            course_schedule = CourseSchedule.objects.filter(id=course_id).first()
            if CourseSchedule.objects.filter(course_code=course_code).exclude(id=course_id).exists():
                data = {
                    'message': 'course already exists'
                }
                return Response(data, status=status.HTTP_302_FOUND)
            course_schedule.course_location = course_location
            course_schedule.course_title = course_title
            course_schedule.course_code = course_code
            course_schedule.level = level
            course_schedule.day = day
            course_schedule.start_time = start_time
            course_schedule.end_time = end_time
            course_schedule.department = department
            course_schedule.is_elective = is_elective
            course_schedule.geofencing = geo_fencing
            course_schedule.save()
            User = get_user_model()
            if course_schedule.is_elective:
                course_schedule.number_of_students = int(number_of_students)
                course_schedule.save()
            else: 
                students = User.objects.filter(department=course_schedule.department, level=course_schedule.level, is_staff=False).count()
                course_schedule.number_of_students = students
                course_schedule.save()
            if schedule_status == 'In Progress':
                courses = CourseSchedule.objects.filter(level=course_schedule.level, schedule_status='In Progress')
                if not courses:
                    course_schedule.schedule_status = schedule_status
                    course_schedule.save()
                else:
                    data = {
                        'message': 'There is already a course in progress'
                    }
                    return Response(data, status=status.HTTP_200_OK)
            else:
                course_schedule.schedule_status = schedule_status
                course_schedule.save()
            
            data = {
                'message': 'course updated successfully'
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            data = {
                'message': 'you are not authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        

    def delete(self, request):
        user = request.user
        if user.is_staff:
            course_id = request.data.get('course_id')
            try:
                course_schedule = CourseSchedule.objects.filter(id=course_id).first()
                course_schedule.delete()
                data = {
                    'message': 'Course deleted successfully'
                }
                return Response(data, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                data = {
                    'message': 'An error occured'
                }
                return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            data = {
                'message': 'you are not authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)

        

class GetCourseListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        courses = CourseSchedule.objects.filter(lecturer=user)
        serializer = CourseListSerializer(courses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetCourseScheduleDetails(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        course_id = request.query_params.get('course_id')
        course_schedule = CourseSchedule.objects.filter(id=course_id).first()
        if course_schedule:
            serializer = CourseScheduleSerializer(course_schedule)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            data = {
                'message': 'no course'
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)
        


class GetCourseScheduleSessionDetails(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        course_id = request.query_params.get('course_id')
        course_schedule = CourseSchedule.objects.filter(id=course_id).first()
        session_id = ''
        if course_schedule:
            attendance_session = AttendanceSession.objects.filter(course=course_schedule, schedule_status='Session Active').first()
            if attendance_session:
                session_id = attendance_session.session_id
            serializer = CourseScheduleSerializer(course_schedule)
            data = {
                'course': serializer.data,
                'session_id': session_id
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            data = {
                'message': 'no course'
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)



class GetRemainingSecondsForStudentOTPpageView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        course_code = request.query_params.get('course_code')
        attendance_session = AttendanceSession.objects.filter(course_code= course_code,schedule_status='Session Active').first()
        if attendance_session:
            local_time = timezone.localtime(
                        attendance_session.expires_at
                    )
            local_now = timezone.localtime(timezone.now())
            remaining_seconds = int(
                (local_time - local_now).total_seconds()
            )
            data = {
                'remaining_seconds': remaining_seconds
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            data = {
                'message': 'no active session'
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)




class CreateAttendanceSessionView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # get attendance session for the session page
    def get(self, request):
        user = request.user
        if user.is_staff:
            attendance_session = AttendanceSession.objects.filter(lecturer=user, schedule_status='Session Active').first()
            attendance_record = AttendanceRecord.objects.filter(session=attendance_session).order_by('-date')
            if attendance_session:
                print(attendance_session.lattitude)
                print(attendance_session.longitude)
                session_serializer = AttendanceSessionSerializer(attendance_session)
                attendance_record_serializer = AttendanceRecordSerializer(attendance_record, many=True)
                local_time = timezone.localtime(
                    attendance_session.expires_at
                )
                local_now = timezone.localtime(timezone.now())
                remaining_seconds = int(
                    (local_time - local_now).total_seconds()
                )
                qr_image_url = request.build_absolute_uri(
                        attendance_session.qr_image.url
                    )
               
                data = {
                    'message': 'active session',
                    'session': session_serializer.data,
                    'attendance_record': attendance_record_serializer.data,
                    'remaining_seconds': remaining_seconds,
                    'qr_image_url': qr_image_url
                }
                return Response(data, status=status.HTTP_200_OK)
            else:
                data = {
                    'message': 'no session'
                }
                return Response(data, status=status.HTTP_404_NOT_FOUND)
        else:
            data = {
                'message': 'you are not authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)


    # create attendance session
    def post(self, request):
        user = request.user
        if user.is_staff:
            course_code = request.data.get('course_code')
            lattitude = float(request.data.get('lattitude'))
            longitude = float(request.data.get('longitude'))
            print(longitude)
            print(lattitude)
            number_of_minutes = user.token_expiration_time
            token = str(uuid.uuid4().int)[:6]
            session_id = str(uuid.uuid4())[:12]
            course = CourseSchedule.objects.filter(course_code=course_code).first()
            today = datetime.now()
            now = timezone.localtime().time()
            today_name = today.strftime('%A')
            local_now = timezone.localtime(timezone.now())
            exp_time = user.token_expiration_time
            if exp_time:
                minutes = exp_time
            else:
                minutes = 30
            expires_at = local_now + timezone.timedelta(minutes=minutes)
            if course.day != today_name or (course.start_time > now or course.end_time < now) :
                data = {
                    'message': f"you don't have any lecture for {course.course_code} scheduled for today or now"
                }
                return Response(data, status=status.HTTP_404_NOT_FOUND)
            if AttendanceSession.objects.filter(lecturer=user, schedule_status='Session Active').exists():
                data = {
                    'message': 'you already have an active session'
                }
                return Response(data, status=status.HTTP_302_FOUND)
            
            attendance_session = AttendanceSession.objects.create(lecturer=user, session_id=session_id, course=course, course_title=course.course_title, course_code=course.course_code,
                                                   course_location=course.course_location, level=course.level, start_time=course.start_time, end_time=course.end_time,longitude=longitude,
                                                   geofencing=course.geofencing, total_student=course.number_of_students, present=0, absent=course.number_of_students,lattitude=lattitude,
                                                   expires_at=expires_at, token=token, attendance_rate=0)
            qr_data = {
              'session_id': session_id
            }
            qr = qrcode.make(qr_data)
            buffer = BytesIO()
            qr.save(buffer, format='PNG')
            filename = f'{course_code}_{token}.png'
            attendance_session.qr_image.save(
                filename,
                ContentFile(buffer.getvalue()),
                save=True
            )
            data = {
                'message': 'Attendance session started'
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            data = {
                'message': 'you are not authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        

    # refresh attendance session
    def patch(self, request):
        user = request.user
        session_id = request.data.get('session_id')
        if user.is_staff:
            session = AttendanceSession.objects.filter(session_id=session_id, lecturer=user).first()
            if session:
                if session.ended_session:
                    data = {
                        'message': 'session already ended'
                    }
                    return Response(data, status=status.HTTP_200_OK)
                local_now = timezone.localtime(timezone.now())
                exp_time = user.token_refresh_time
                if exp_time:
                    minutes = exp_time
                else:
                    minutes = 1
                session.expires_at = local_now + timezone.timedelta(minutes=minutes)
                session.save()
        
                data = {
                    'message': 'attendance session refreshed'
                }
                return Response(data, status=status.HTTP_200_OK)
            else:
                data = {
                    'message': 'no active session'
                }
                return Response(data, status=status.HTTP_200_OK)
        else:
            data = {
                'message': 'you are not authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)




# end session 
class EndAttendanceSessionView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        session_id = request.data.get('session_id')
        if user.is_staff:
            session = AttendanceSession.objects.filter(session_id=session_id, lecturer=user).first()
            if session:
                if session.ended_session:
                    data = {
                        'message': 'session already ended'
                    }
                    return Response(data, status=status.HTTP_200_OK)
                course = session.course
                course_session = AttendanceSession.objects.filter(course=course, lecturer=user)
                total_session_percentage = 0
                num_of_sessions = 0
                for sessions in course_session:
                    total_session_percentage += sessions.attendance_rate
                    num_of_sessions += 1
                if total_session_percentage > 0:
                    course_attendance_percentage = ((total_session_percentage / 100) / num_of_sessions) * 100
                    course.attendance_rate = round(course_attendance_percentage)
                    course.save()
                session.schedule_status = 'Session Ended'
                session.ended_session = True
                session.save()
                course.schedule_status = 'Ended'
                course.save()
                data = {
                    'message': 'session ended successfully'
                }
                return Response(data, status=status.HTTP_200_OK)
            else:
                data = {
                    'message': 'no active session'
                }
                return Response(data, status=status.HTTP_404_NOT_FOUND)
        else:
            data = {
                'message': 'you are not authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)




class AttendanceSessionDashboardView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # attendance session for lecturer dashboard
    def get(self, request):
        user = request.user
        if user.is_staff:
            attendance_session = AttendanceSession.objects.filter(lecturer=user, schedule_status='Session Active').first()
            if attendance_session:
                session_serializer = AttendanceSessionSerializer(attendance_session)
                remaining_seconds = int(
                    (attendance_session.expires_at - timezone.now()).total_seconds()
                )
                data = {
                    'message': 'active session',
                    'remaining_seconds': remaining_seconds,
                    'session': session_serializer.data,
                }
                return Response(data, status=status.HTTP_200_OK)
            else:
                data = {
                    'message': 'no session'
                }
                return Response(data, status=status.HTTP_404_NOT_FOUND)
        else:
            data = {
                'message': 'you are not authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        


class QRCodeAttendanceview(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # signing attendance through qr code 
    def post(self, request):
        user = request.user
        if not user.is_staff:
            session_id = request.data.get('session_id')
            student_longitude = request.data.get('longitude')
            student_lattitude = request.data.get('lattitude')
            if isinstance(session_id, str) and session_id.startswith('{'):
                session_id = ast.literal_eval(session_id)
                session_id = session_id['session_id']
            print(request.data)
            session = AttendanceSession.objects.filter(session_id=session_id).first()
            if not session:
                data = {
                    'message': 'invalid qr code'
                }
                return Response(data, status=status.HTTP_404_NOT_FOUND)
            course = session.course
            lecturer_location = (
                    session.lattitude,
                    session.longitude)
            student_location = (
                student_lattitude,
                student_longitude
            )
            distance = geodesic(
                lecturer_location,
                student_location
            ).meters
            if session.expires_at > timezone.now() or session.ended_session:
                if distance <= session.geofencing:
                    if not AttendanceRecord.objects.filter(student=user, session=session).exists():
                        attendance_record = AttendanceRecord.objects.create(student=user, first_name=user.first_name, last_name=user.last_name, matric_number=user.matric_number,
                                                                            level=user.level, department=user.department, course=course, course_title=course.course_title, course_code=course.course_code, status='Present', method='QR Code',
                                                                            lecturer=session.lecturer, time=timezone.localtime().time(), session=session)
                        session.present += 1
                        session.absent -= 1
                        session.save()
                        percentage = (session.present/session.total_student) * 100
                        session.attendance_rate = percentage
                        session.save()
                        student_record = AttendanceRecord.objects.filter(student=user, course=course).count()
                        number_of_classes = AttendanceSession.objects.filter(course=course).count()
                        student_percentage = (student_record / number_of_classes) * 100
                        lecturer = session.lecturer
                        if not StudentCourseCard.objects.filter(student=user, course=course).exists():
                            course_card = StudentCourseCard.objects.create(student=user, first_name=user.first_name, last_name=user.last_name, email=user.email, course=course, attendance_score=0,
                                                                           matric_number=user.matric_number, course_code=course.course_code, level=user.level, department=user.department, lecturer=course.lecturer)
                        student_course_card = StudentCourseCard.objects.filter(student=user, course=course).first()
                        if student_percentage >= lecturer.minimum_attendance:
                            student_course_card.eligible_for_exam = True
                            student_course_card.save()
                        else:
                            student_course_card.eligible_for_exam = False
                            student_course_card.save()
                        student_course_card.attendance_percentage = student_percentage
                        student_course_card.save()
                        student_attendance_score = (student_percentage / 100) * 5
                        student_course_card.attendance_score = round(student_attendance_score)
                        student_course_card.save()

                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.group_send)(
                            session_id,
                            {
                                'type': 'display_live_attendance',
                                'session_id': session_id
                            }
                        )

                        data ={ 
                            'message': 'attendance marked'
                        }
                        return Response(data, status=status.HTTP_200_OK)
                    else:
                        data = {
                            'message': 'attendance already marked'
                        }
                        return Response(data, status=status.HTTP_200_OK)
                else:
                    data = {
                        'message': 'out of range'
                    }
                    return Response(data, status=status.HTTP_401_UNAUTHORIZED)
            else:
                data = {
                    'message': 'expired or ended attendance session'
                }
                return Response(data, status=status.HTTP_403_FORBIDDEN)
        else:
            data = {
                'data': 'only students can access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)


class TokenAttendanceview(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # signing attendance through otp code 
    def post(self, request):
        user = request.user
        if not user.is_staff:
            token = request.data.get('token')
            student_longitude = request.data.get('longitude')
            student_lattitude = request.data.get('lattitude')
            print('token:', token)
            session = AttendanceSession.objects.filter(token=token).first()
            if not session:
                data = {
                    'message': 'invalid otp code'
                }
                return Response(data, status=status.HTTP_404_NOT_FOUND)
            course = session.course
            lecturer_location = (
                    session.lattitude,
                    session.longitude)
            student_location = (
                student_lattitude,
                student_longitude
            )
            distance = geodesic(
                lecturer_location,
                student_location
            ).meters
            if session.expires_at > timezone.now() or session.ended_session:
                if distance <= session.geofencing:
                    if not AttendanceRecord.objects.filter(student=user, session=session).exists():
                        attendance_record = AttendanceRecord.objects.create(student=user, first_name=user.first_name, last_name=user.last_name, matric_number=user.matric_number,
                                                                            level=user.level, department=user.department, course=course, course_title=course.course_title, course_code=course.course_code, status='Present', method='Token',
                                                                            lecturer=session.lecturer, time=timezone.localtime().time(), session=session)
                        session.present += 1
                        session.absent -= 1
                        session.save()
                        percentage = (session.present/session.total_student) * 100
                        session.attendance_rate = percentage
                        session.save()
                        student_record = AttendanceRecord.objects.filter(student=user, course=course).count()
                        number_of_classes = AttendanceSession.objects.filter(course=course).count()
                        student_percentage = (student_record / number_of_classes) * 100
                        lecturer = session.lecturer
                        if not StudentCourseCard.objects.filter(student=user, course=course).exists():
                            course_card = StudentCourseCard.objects.create(student=user, first_name=user.first_name, last_name=user.last_name, email=user.email, course=course,attendance_score=0, 
                                                                           matric_number=user.matric_number, course_code=course.course_code, level=user.level, department=user.department, lecturer=course.lecturer)
                        student_course_card = StudentCourseCard.objects.filter(student=user, course=course).first()
                        if student_percentage >= lecturer.minimum_attendance:
                            student_course_card.eligible_for_exam = True
                            student_course_card.save()
                        else:
                            student_course_card.eligible_for_exam = False
                            student_course_card.save()
                        student_course_card.attendance_percentage = student_percentage
                        student_course_card.save()
                        student_attendance_score = (student_percentage / 100) * 5
                        student_course_card.attendance_score = round(student_attendance_score)
                        student_course_card.save()
                        print(type(str(session.session_id)), str(session.session_id))
                        print("Sending to group:", str(session.session_id))

                        channel_layer = get_channel_layer()
                        print("Before group_send")
                        async_to_sync(channel_layer.group_send)(
                            str(session.session_id),
                            {
                                'type': 'display_live_attendance',
                                'session_id': session.session_id
                            }
                        )
                        print("After group_send")

                        data = {
                            'message': 'attendance marked'
                        }
                        return Response(data, status=status.HTTP_200_OK)
                    else:
                        data = {
                            'message': 'attendance already marked'
                        }
                        return Response(data, status=status.HTTP_200_OK)
                else:
                    data = {
                        'message': 'out of range'
                    }
                    return Response(data, status=status.HTTP_401_UNAUTHORIZED)
            else:
                data = {
                    'message': 'expired or ended attendance session'
                }
                return Response(data, status=status.HTTP_403_FORBIDDEN)
        else:
            data = {
                'data': 'only students can access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)



class AttendanceHistoryView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # attendance history for student history page
    def get(self, request):
        user = request.user
        if not user.is_staff:
            attendance_record = AttendanceRecord.objects.filter(student=user).order_by('-date')
            serializer = AttendanceHistorySerializer(attendance_record, many=True)
            data = {
                'data': serializer.data
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            data = {
                'data': 'only students can access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
    


class RecentActivityView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # recent activity for dashboard
    def get(self, request):
        user = request.user
        if not user.is_staff:
            today_date = timezone.localdate()
            attendance_record = AttendanceRecord.objects.filter(student=user, date__date = today_date ).order_by('-date')[:5]
            serializer = AttendanceHistorySerializer(attendance_record, many=True)
            data = {
                'data': serializer.data
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            data = {
                'data': 'only students can access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
    
