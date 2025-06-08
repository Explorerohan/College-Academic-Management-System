from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .models import User

# Create your views here.

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'teacher':
                return redirect('teacher_dashboard')
            elif user.role == 'student':
                return redirect('student_dashboard')
            else:
                return redirect('admin:index')
    return render(request, 'users/login.html')

@login_required
def teacher_dashboard(request):
    if request.user.role != 'teacher':
        return redirect('login')
    students = User.objects.filter(role='student')
    return render(request, 'users/teacher_dashboard.html', {'students': students})

@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('login')
    return render(request, 'users/student_dashboard.html')
