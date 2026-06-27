from django.urls import path
from . import views

urlpatterns = [
    path('course-schedule/', views.CourseScheduleView.as_view(), name='course_schedule'),

    path('present-course/', views.PresentCourseView.as_view(), name='present_course'),

    path('dashboard-courseview/', views.LecturerCoursesView.as_view(), name='lecturer_dashboard_course_view'),

    path('course-management/', views.LecturerCoursesManagementView.as_view(), name='lecturer_course_management'),

    path('attendance-session/', views.CreateAttendanceSessionView.as_view(), name='attendance_session'),

    path('end-session/', views.EndAttendanceSessionView.as_view(), name='end_session'),

    path('attendance-session-dashboard/', views.AttendanceSessionDashboardView.as_view(), name='attendance_session_dashboard'),

    path('qrcode-attendance/', views.QRCodeAttendanceview.as_view(), name='qrcode_attendance'),

    path('token-attendance/', views.TokenAttendanceview.as_view(), name='token_attendance'),

    path('attendance-history/', views.AttendanceHistoryView.as_view(), name='attendance_history'),

    path('recent-activity', views.RecentActivityView.as_view(), name='recent_activity'),

    path('course-details/', views.GetCourseScheduleDetails.as_view(), name='course_details'),

    path('course-details-session/', views.GetCourseScheduleSessionDetails.as_view(), name='course_details_session'),

    path('course-list/', views.GetCourseListView.as_view(), name='course_list'),

    path('get-remaining-seconds/', views.GetRemainingSecondsForStudentOTPpageView.as_view(), name='get_remaining_seconds')
]