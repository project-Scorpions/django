from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.student_register, name='student_register'),
    path('', views.student_login, name='student_login'),
    path('home/', views.student_home, name='student_home'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('courses/', views.student_courses, name='student_courses'),
    path('enrollment/', views.student_enrollment, name='enrollment'),
    path('schedule/', views.student_schedule, name='my_schedule'),
    path('academic-history/', views.academic_history, name='academic_history'),
    path('enrollment/submit/', views.submit_enrollment, name='submit_enrollment'),
    path('enrollment/get-schedules/', views.GetSchedulesView.as_view(), name='get_schedules'),
    path('get-courses/', views.get_courses, name='get_courses'),
    path('enrollment/<int:enroll_id>/details/', views.enrollment_details, name='enrollment_details'),
    path('add-remarks/<int:enroll_id>/', views.add_academic_remarks, name='add_academic_remarks'),
    path('view-academic-history/<int:stud_id>/', views.view_academic_history, name='view_academic_history'),
    path('select-enrollment/<int:stud_id>/', views.select_enrollment_for_remarks, name='select_enrollment_for_remarks'),
]
