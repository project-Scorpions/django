from django.urls import path
from . import views

urlpatterns = [
    # Admin Portal URLs
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('students/', views.student_records, name='student_records'),
    path('enrollments/', views.pending_enrollment, name='pending_enrollment'),
    path('enrollments/approve/<int:enroll_id>/', views.approve_enrollment, name='approve_enrollment'),
    path('enrollments/reject/<int:enroll_id>/', views.reject_enrollment, name='reject_enrollment'),
    path('courses/', views.admin_courses, name='admin_courses'),
    path('schedules/', views.admin_schedules, name='admin_schedules'),
    
#   # Authentication URLs
#     path('login/', views.student_login, name='student_login'),
#     path('logout/', views.logout_view, name='logout'),  
]