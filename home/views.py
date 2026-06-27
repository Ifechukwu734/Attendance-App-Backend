from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .serializers import ReturnCustomUserSerializer, ReturnLecturerSerializer, FaceVerificationSerializer
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from courseManagement.models import CourseSchedule, AttendanceRecord, AttendanceSession, StudentCourseCard
from courseManagement.serializers import CourseScheduleSerializer, AttendanceRecordSerializer, StudentCourseCardSerializer, AttendanceSessionSerializer
from django.utils import timezone
from django.db.models import Q 
from django.db import IntegrityError
from openpyxl import Workbook
from openpyxl.styles import Font
from deepface import DeepFace
import os
import tempfile
from geopy.distance import geodesic

# Create your views here.


# Student Login
class StudentLoginView(APIView):

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        device_id = request.data.get('device_id')

        user = authenticate(email=email, password=password)
        if user is not None:
            User = get_user_model()
            auth_user = get_object_or_404(User, email=email)
            if auth_user.is_staff:
                data = {
                    'message': 'Only students are authorized to access this page'
                }
                return Response(data, status=status.HTTP_401_UNAUTHORIZED)
            if Token.objects.filter(user=auth_user).exists():
                old_token = Token.objects.filter(user=auth_user).first()
                old_token.delete()
            if auth_user.device_id == '':
                token, created = Token.objects.get_or_create(user=user)
                serializer = ReturnCustomUserSerializer(auth_user)
                data = {
                    'message': 'login successful',
                    'hint': "first time",
                    'token': token.key,
                    'data': serializer.data
                }
                return Response(data, status=status.HTTP_200_OK)
            elif auth_user.device_id == device_id:
                token, created = Token.objects.get_or_create(user=user)
                serializer = ReturnCustomUserSerializer(auth_user)
                data = {
                    'message': 'login successful',
                    'hint': "same device",
                    'token': token.key,
                    'data': serializer.data
                }
                return Response(data, status=status.HTTP_200_OK)
            else:
                token, created = Token.objects.get_or_create(user=user)
                serializer = ReturnCustomUserSerializer(auth_user)
                data = {
                    'message': 'login successful',
                    'hint': "different device",
                    'token': token.key,
                    'data': serializer.data
                }
                return Response(data, status=status.HTTP_200_OK)
            
        else:
            data = {
                'message': 'invalid credentials'
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)


class UploadFaceVerificationImage(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        image = request.FILES.get('image')
        device_id = request.data.get('device_id')
        if user.is_staff:
            data = {
                'message': 'Only students are authorized to access this page'
            }
            print(data)
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        user.verification_face = image
        user.face_verification = True
        user.save()
        user.device_id = device_id
        user.save()
        data = {
            'image': 'image uploaded successfully'
        }
        return Response(data, status=status.HTTP_200_OK)
        


class FaceVerificationView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        device_id = request.data.get('device_id')
        # user.device_id = ''
        # user.save()
        if user.is_staff:
            data = {
                'message': 'Only students are authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        try:
            serializer = FaceVerificationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            image = serializer.validated_data['verification_face']
            print(image)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                for chunk in image.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name
                print(temp_path)
                # faces = DeepFace.extract_faces(
                #     img_path=temp_path,
                #     enforce_detection=True,
                # )

                # print(faces)

            try:
                result = DeepFace.verify(img1_path=user.verification_face.path, img2_path=temp_path, model_name='Facenet512', enforce_detection=False)
                if result['distance'] <= 0.4:
                    user.device_id = device_id
                    user.save()
                    data = {
                        'verified': result['verified'],
                        'distance': result['distance'],
                        'threshold': result['threshold']
                    }
                    print(data)
                    return Response(data, status=status.HTTP_200_OK)
                else:
                    data = {
                        'verified': result['verified'],
                        'distance': result['distance'],
                        'threshold': result['threshold']
                    }
                    print(data)
                    return Response(data, status=status.HTTP_404_NOT_FOUND)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        except Exception as e:
            print(e)
            data = {
                'message': 'error verifying face'
            }
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Lecturer Login
class LecturerLoginView(APIView):

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(email=email, password=password)
        if user is not None:
            User = get_user_model()
            auth_user = get_object_or_404(User, email=email)
            if auth_user.is_staff:
                token, created = Token.objects.get_or_create(user=user)
                serializer = ReturnLecturerSerializer(auth_user)
                data = {
                    'message': 'login successful',
                    'token': token.key,
                    'data': serializer.data
                }
                return Response(data, status=status.HTTP_200_OK)
            else:
                data = {
                    'message': 'only staffs are authorized to access this page'
                }
                return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        else:
            data = {
                'message': 'invalid credentials'
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)




# Student Profile Info
class DisplayStudentDetailsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_staff:
            data = {
                'message': 'only students can access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        serializer = ReturnCustomUserSerializer(user)
        data = {
            'data': serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)
    


# Lecturer Profile Info
class DisplayLecturerDetailsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_staff:
            serializer = ReturnLecturerSerializer(user)
            profile_image_url = request.build_absolute_uri(
                        user.profile_image.url
                    )
            data = {
                'profile_image': profile_image_url,
                'data': serializer.data
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            data = {
                'message': 'you are not authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)


    # update lecturer profile
    def patch(self, request):
        user = request.user
        if user.is_staff:
            try:
                profile_image = request.FILES.get('profile_image')
                serializer = ReturnLecturerSerializer(user, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    if profile_image:
                        user.profile_image = profile_image
                        user.save()
                    
                    data = {
                        'message': 'profile updated'
                    }
                    return Response(data, status=status.HTTP_200_OK)
                else:
                    print(serializer.errors)
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except IntegrityError:
                data = {
                    'message': 'email already exists'
                }
                return Response(data, status=status.HTTP_302_FOUND)
        else:
            data = {
                'message': 'you are not authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)



class LecturerLogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            token = get_object_or_404(Token, user=user)
            token.delete()
            data = {
                'message': 'Logout successful'
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            data = {
                'message': 'Error Logging out'
            }
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class StudentLogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            # user.device_id = ''
            # user.save()
            token = get_object_or_404(Token, user=user)
            token.delete()
            data = {
                'message': 'Logout successful'
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            data = {
                'message': 'Error Logging out'
            }
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# Lecturer Dashboard Info
class DisplayLecturerDetails(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        User = get_user_model()
        if user.is_staff:
            serializer = ReturnLecturerSerializer(user)
            number_of_courses = CourseSchedule.objects.filter(lecturer=user).count()
            courses = CourseSchedule.objects.filter(lecturer=user)
            profile_image_url = request.build_absolute_uri(
                        user.profile_image.url
                    )
            total_number_of_students = 0
            for course in courses:
                students = course.number_of_students
                total_number_of_students += students
            if total_number_of_students > 0:
                attendance_today = AttendanceRecord.objects.filter(date__date=timezone.localdate(), lecturer=user).count()
                attendance_today_result = ((attendance_today / total_number_of_students) / number_of_courses) * 100
                attendance_today_percentage = round(attendance_today_result)
                data = {
                    'total_number_of_students': total_number_of_students,
                    'number_of_courses': number_of_courses,
                    'attendance_today_percentage': attendance_today_percentage,
                    'number_of_attendance_today': attendance_today,
                    'lecturer_profile': serializer.data,
                    'profile_image': profile_image_url
                }
                return Response(data, status=status.HTTP_200_OK)
            else:
                data = {
                    'total_number_of_students': total_number_of_students,
                    'number_of_courses': number_of_courses,
                    'attendance_today_percentage': 0,
                    'number_of_attendance_today': 0,
                    'lecturer_profile': serializer.data,
                    'profile_image': profile_image_url
                }
                return Response(data, status=status.HTTP_200_OK)

        else:
            data = {
                'message': 'you are not authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        



        
#Recent Attendance Record in Lecturer Dashboard
class RecentAttendanceRecordView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_staff:
            attendance_record = AttendanceRecord.objects.filter(lecturer=user, date__date=timezone.localdate()).order_by('-time')[:5]
            serializer = AttendanceRecordSerializer(attendance_record, many=True)
            data = {
                'data': serializer.data
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            data = {
                'message': 'you are not authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        


# getting student attendance details in lecturer student page
class StudentPageView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        course_code = request.query_params.get('course_code')
        search = request.query_params.get('search')
        if user.is_staff:
            if search and course_code:
                course_card = StudentCourseCard.objects.filter(Q(first_name__icontains=search, course_code=course_code, lecturer=user) | Q(last_name__icontains=search, course_code=course_code, lecturer=user) ).order_by('first_name')
                if not course_card:
                    data = {
                        'data': 'no item found'
                    }
                    return Response(data, status=status.HTTP_404_NOT_FOUND)
                number_of_students = course_card.count()
                num_of_eligible = 0
                num_of_defaulters = 0
                for student in course_card:
                    if student.eligible_for_exam:
                        num_of_eligible += 1
                    else:
                        num_of_defaulters += 1
                serializer = StudentCourseCardSerializer(course_card, many=True)
                data = {
                    'total_students': number_of_students,
                    'num_of_eligible': num_of_eligible,
                    'num_of_defaulter': num_of_defaulters,
                    'data': serializer.data,
                    'search': search,
                    'course_code': course_code
                }
                return Response(data, status=status.HTTP_200_OK)
            
            elif search:
                course_card = StudentCourseCard.objects.filter(Q(first_name__icontains=search, lecturer=user) | Q(last_name__icontains=search, lecturer=user) ).order_by('first_name')
                if not course_card:
                    data = {
                        'data': 'no item found'
                    }
                    return Response(data, status=status.HTTP_404_NOT_FOUND)
                number_of_students = course_card.count()
                num_of_eligible = 0
                num_of_defaulters = 0
                for student in course_card:
                    if student.eligible_for_exam:
                        num_of_eligible += 1
                    else:
                        num_of_defaulters += 1
                serializer = StudentCourseCardSerializer(course_card, many=True)
                data = {
                    'total_students': number_of_students,
                    'num_of_eligible': num_of_eligible,
                    'num_of_defaulter': num_of_defaulters,
                    'data': serializer.data,
                    'search': search,
                    'course_code': course_code
                }
                return Response(data, status=status.HTTP_200_OK)
            
            elif course_code:
                course_card = StudentCourseCard.objects.filter(course_code=course_code, lecturer=user).order_by('first_name')
                if not course_card:
                    data = {
                        'data': 'no item found'
                    }
                    return Response(data, status=status.HTTP_404_NOT_FOUND)
                number_of_students = course_card.count()
                num_of_eligible = 0
                num_of_defaulters = 0
                for student in course_card:
                    if student.eligible_for_exam:
                        num_of_eligible += 1
                    else:
                        num_of_defaulters += 1
                serializer = StudentCourseCardSerializer(course_card, many=True)
                data = {
                    'total_students': number_of_students,
                    'num_of_eligible': num_of_eligible,
                    'num_of_defaulter': num_of_defaulters,
                    'data': serializer.data,
                    'search': search,
                    'course_code': course_code
                }
                return Response(data, status=status.HTTP_200_OK)
            
            selected_course = CourseSchedule.objects.filter(course_code=course_code).first()
            course_card = StudentCourseCard.objects.filter(course=selected_course)
            number_of_students = course_card.count()
            num_of_eligible = 0
            num_of_defaulters = 0
            for student in course_card:
                if student.eligible_for_exam:
                    num_of_eligible += 1
                else:
                    num_of_defaulters += 1
            serializer = StudentCourseCardSerializer(course_card, many=True)
            data = {
                'total_students': number_of_students,
                'num_of_eligible': num_of_eligible,
                'num_of_defaulter': num_of_defaulters,
                'data': serializer.data,
                'search': search,
                'course_code': course_code
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            data = {
                'message': 'you are not authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        


# exporting session attendance record
class ExportLiveAttendanceRecord(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        session_id = request.data.get('session_id')
        if user.is_staff:
            session = AttendanceSession.objects.filter(session_id=session_id).first()
            if session:
                work_book = Workbook()
                work_sheet = work_book.active
                work_sheet.title = f'Students Attendance Record for {session.course_code} session {session.session_id} {timezone.now()}'
                
                # headers
                work_sheet.append([
                    'Student',
                    'Matric Number',
                    'Method',
                    'Time',
                    'Status'
                ])

                #data
                data = AttendanceRecord.objects.filter(session=session).order_by('first_name')
                for students in data:
                    work_sheet.append([
                        f'{students.first_name} {students.last_name}',
                        students.matric_number,
                        students.method,
                        students.method,
                        students.status
                    ])

                # making the headers bold
                for cell in work_sheet[1]:
                    cell.font = Font(bold=True)
                
                # autosizing columns
                for column in work_sheet.columns:
                    max_length = max(
                        len(str(cell.value or ""))
                        for cell in column
                    )
                    work_sheet.column_dimensions[
                        column[0].column_letter
                    ].width = max_length + 5

                response = HttpResponse(
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = (
                    f'attachment; filename="{session.course_code}-{timezone.now()}"'
                )
                work_book.save(response)
                return response
            else:
                data = {
                    'message': 'invalid session id'
                }
                return Response(data, status=status.HTTP_404_NOT_FOUND)
        else:
            data = {
                'message': 'you are not authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)





# exporting student attendance details
class ExportStudentPageView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        course_code = request.query_params.get('course_code')
        search = request.query_params.get('search')
        if user.is_staff:
            work_book = Workbook()
            work_sheet = work_book.active
            work_sheet.title = f'Student Details'
            if search and course_code:
                course_card = StudentCourseCard.objects.filter(Q(first_name__icontains=search, course_code=course_code, lecturer=user) | Q(last_name__icontains=search, course_code=course_code, lecturer=user) ).order_by('first_name')
                if not course_card:
                    data = {
                        'data': 'no item found'
                    }
                    return Response(data, status=status.HTTP_404_NOT_FOUND)
                work_sheet.append([
                    'Student',
                    'Matric Number',
                    'Level',
                    'Course',
                    'Attendance',
                    'Eligibility'
                ])

                for students in course_card:
                    work_sheet.append([
                        f'{students.first_name} {students.last_name}',
                        students.matric_number,
                        students.level,
                        students.course_code,
                        students.attendance_percentage,
                        students.eligible_for_exam
                    ])

                # making the headers bold
                for cell in work_sheet[1]:
                    cell.font = Font(bold=True)
                
                # autosizing columns
                for column in work_sheet.columns:
                    max_length = max(
                        len(str(cell.value or ""))
                        for cell in column
                    )
                    work_sheet.column_dimensions[
                        column[0].column_letter
                    ].width = max_length + 5

                response = HttpResponse(
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = (
                    f'attachment; filename="Student Details-{timezone.now()}'
                )
                work_book.save(response)
                return response
            elif search:
                course_card = StudentCourseCard.objects.filter(Q(first_name__icontains=search, lecturer=user) | Q(last_name__icontains=search, lecturer=user) ).order_by('first_name')
                if not course_card:
                    data = {
                        'data': 'no item found'
                    }
                    return Response(data, status=status.HTTP_404_NOT_FOUND)
                work_sheet.append([
                    'Student',
                    'Matric Number',
                    'Level',
                    'Course',
                    'Attendance',
                    'Eligibility'
                ])

                for students in course_card:
                    work_sheet.append([
                        f'{students.first_name} {students.last_name}',
                        students.matric_number,
                        students.level,
                        students.course_code,
                        students.attendance_percentage,
                        students.eligible_for_exam
                    ])

                # making the headers bold
                for cell in work_sheet[1]:
                    cell.font = Font(bold=True)
                
                # autosizing columns
                for column in work_sheet.columns:
                    max_length = max(
                        len(str(cell.value or ""))
                        for cell in column
                    )
                    work_sheet.column_dimensions[
                        column[0].column_letter
                    ].width = max_length + 5

                response = HttpResponse(
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = (
                    f'attachment; filename="Student Details-{timezone.now()}'
                )
                work_book.save(response)
                return response
            
            selected_course = CourseSchedule.objects.filter(course_code=course_code).first()
            course_card = StudentCourseCard.objects.filter(course=selected_course)
            work_sheet.append([
                    'Student',
                    'Matric Number',
                    'Level',
                    'Course',
                    'Attendance',
                    'Eligibility'
                ])

            for students in course_card:
                work_sheet.append([
                    f'{students.first_name} {students.last_name}',
                    students.matric_number,
                    students.level,
                    students.course_code,
                    students.attendance_percentage,
                    students.eligible_for_exam
                ])

            # making the headers bold
            for cell in work_sheet[1]:
                cell.font = Font(bold=True)
            
            # autosizing columns
            for column in work_sheet.columns:
                max_length = max(
                    len(str(cell.value or ""))
                    for cell in column
                )
                work_sheet.column_dimensions[
                    column[0].column_letter
                ].width = max_length + 5

            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = (
                f'attachment; filename="Student Details-{timezone.now()}'
            )
            work_book.save(response)
            return response
        else:
            data = {
                'message': 'you are not authorized to access this page'
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)
        


class CheckGeofencingRadius(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')
        student_longitude = request.data.get('longitude')
        student_lattitude = request.data.get('lattitude')
        print(student_lattitude)
        print(student_longitude)
        session = AttendanceSession.objects.filter(session_id=session_id).first()
        if not session:
            data = {
                'message': 'invalid  session id'
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)
        serializer = AttendanceSessionSerializer(session)
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
        if distance <= session.geofencing:
            data = {
                'message': 'you are within the class location',
                'distance': round(distance),
                'data': serializer.data
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            data = {
                'message': 'you are not within the class location',
                'distance': round(distance),
                'data': serializer.data
            }
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)