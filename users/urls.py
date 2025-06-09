from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Teacher URLs
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/students/<int:student_id>/', views.teacher_student_detail, name='teacher_student_detail'),
    path('teacher/announcements/create/', views.teacher_create_announcement, name='teacher_create_announcement'),
    path('teacher/announcements/create/<int:student_id>/', views.teacher_create_student_announcement, name='teacher_create_student_announcement'),
    path('teacher/results/add/<int:student_id>/', views.teacher_add_result, name='teacher_add_result'),
    path('teacher/announcements/', views.teacher_announcements, name='teacher_announcements'),
    path('teacher/results/', views.teacher_results, name='teacher_results'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    
    # Student URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/announcements/', views.student_announcements, name='student_announcements'),
    path('student/results/', views.student_results, name='student_results'),
    path('student/profile/', views.profile, name='profile'),
    path('student/edit-profile/', views.edit_profile, name='edit_profile'),
] 