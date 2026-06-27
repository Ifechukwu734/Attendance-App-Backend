from django.urls import path
from . import views

urlpatterns = [
    path('student-login/', views.StudentLoginView.as_view(), name='student_login'),

    path('lecturer-login/', views.LecturerLoginView.as_view(), name='lecturer_login'),

    path('student-details/', views.DisplayStudentDetailsView.as_view(), name='student details'),

    path('upload-face/', views.UploadFaceVerificationImage.as_view(), name='upload_face'),

    path('face-verification/', views.FaceVerificationView.as_view(), name='face_verification'),

    path('student-profile/', views.DisplayStudentDetailsView.as_view(), name='student_profile'),

    path('lecturer-profile/', views.DisplayLecturerDetailsView.as_view(), name='lecturer_profile'),

    path('lecturer-dashboard/', views.DisplayLecturerDetails.as_view(), name='lecturer_dashboard'),

    path('dashboard-recent-attendance/', views.RecentAttendanceRecordView.as_view(), name='dashboard_recent_attendance'),

    path('student-page/', views.StudentPageView.as_view(), name='student_page'),

    path('export-live-attendance/', views.ExportLiveAttendanceRecord.as_view(), name='export_live_attendance'),

    path('export-student-details/', views.ExportStudentPageView.as_view(), name='export_student_details'),

    path('check-geofencing/', views.CheckGeofencingRadius.as_view(), name='check_geofencing'),

    path('lecturer-logout/', views.LecturerLogoutView.as_view(), name='lecturer_logout'),

    path('student-logout/', views.StudentLogoutView.as_view(), name='student_logout'),
]