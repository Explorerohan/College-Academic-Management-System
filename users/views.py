from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .models import User, Announcement, Result
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q

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
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')

@login_required
def teacher_dashboard(request):
    if not request.user.is_teacher:
        return redirect('login')
    students = User.objects.filter(role='student')
    return render(request, 'users/teacher_dashboard.html', {'students': students})

@login_required
def teacher_student_detail(request, student_id):
    if not request.user.is_teacher:
        return redirect('login')
    
    student = get_object_or_404(User, id=student_id, role='student')
    student_results = Result.objects.filter(student=student)
    
    context = {
        'student': student,
        'student_results': student_results,
    }
    return render(request, 'users/teacher_student_detail.html', context)

@login_required
def teacher_create_announcement(request):
    if not request.user.is_teacher:
        return redirect('login')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        priority = request.POST.get('priority')
        send_email = request.POST.get('send_email') == 'on'
        
        announcement = Announcement.objects.create(
            title=title,
            content=content,
            priority=priority,
            created_by=request.user
        )
        
        if send_email:
            # Get all student emails
            student_emails = User.objects.filter(role='student').values_list('email', flat=True)
            
            # Send email to all students
            send_mail(
                subject=f'New Announcement: {title}',
                message=f'''
                Priority: {priority.upper()}
                
                {content}
                
                This is an automated message from the Academic Management System.
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(student_emails),
                fail_silently=True,
            )
        
        messages.success(request, 'Global announcement created successfully!')
        return redirect('teacher_announcements')
    
    return render(request, 'users/teacher_create_announcement.html')

@login_required
def teacher_create_student_announcement(request, student_id):
    if not request.user.is_teacher:
        return redirect('login')
    
    student = get_object_or_404(User, id=student_id, role='student')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        priority = request.POST.get('priority')
        send_email = request.POST.get('send_email') == 'on'
        
        announcement = Announcement.objects.create(
            title=title,
            content=content,
            priority=priority,
            created_by=request.user,
            student=student  # Set the specific student
        )
        
        if send_email:
            # Send email only to the specific student
            send_mail(
                subject=f'New Personal Announcement: {title}',
                message=f'''
                Dear {student.get_full_name()},
                
                Priority: {priority.upper()}
                
                {content}
                
                This is a personal announcement from your teacher.
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.email],
                fail_silently=True,
            )
        
        messages.success(request, f'Personal announcement created for {student.get_full_name()}!')
        return redirect('teacher_student_detail', student_id=student.id)
    
    return render(request, 'users/teacher_create_student_announcement.html', {'student': student})

@login_required
def teacher_add_result(request, student_id):
    if not request.user.is_teacher:
        return redirect('login')
    
    student = get_object_or_404(User, id=student_id, role='student')
    
    if request.method == 'POST':
        subject = request.POST.get('subject')
        marks = request.POST.get('marks')
        total_marks = request.POST.get('total_marks')
        grade = request.POST.get('grade')
        remarks = request.POST.get('remarks')
        send_email = request.POST.get('send_email') == 'on'
        
        # Check if result already exists for this subject
        existing_result = Result.objects.filter(student=student, subject=subject).first()
        
        if existing_result:
            # Update existing result
            existing_result.marks_obtained = marks
            existing_result.total_marks = total_marks
            existing_result.grade = grade
            existing_result.remarks = remarks
            existing_result.save()
            result = existing_result
        else:
            # Create new result
            result = Result.objects.create(
                student=student,
                subject=subject,
                marks_obtained=marks,
                total_marks=total_marks,
                grade=grade,
                remarks=remarks,
                created_by=request.user
            )
        
        if send_email:
            # Send email to student
            send_mail(
                subject=f'New Result Published: {subject}',
                message=f'''
                Dear {student.get_full_name()},
                
                Your result for {subject} has been published:
                
                Marks Obtained: {marks}/{total_marks}
                Grade: {grade}
                Percentage: {result.percentage():.2f}%
                
                Remarks: {remarks or 'No remarks'}
                
                This is an automated message from the Academic Management System.
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.email],
                fail_silently=True,
            )
        
        messages.success(request, 'Result saved successfully!')
        return redirect('teacher_student_detail', student_id=student.id)
    
    return render(request, 'users/teacher_add_result.html', {'student': student})

@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('login')
    return render(request, 'users/student_dashboard.html')

@login_required
def student_announcements(request):
    if not request.user.is_student:
        return redirect('login')
    
    # Get both global announcements and student-specific announcements
    announcements = Announcement.objects.filter(
        Q(is_active=True) & (Q(student=None) | Q(student=request.user))
    )
    return render(request, 'users/announcements.html', {'announcements': announcements})

@login_required
def student_results(request):
    if not request.user.is_student:
        return redirect('login')
    
    results = Result.objects.filter(student=request.user)
    return render(request, 'users/results.html', {'results': results})

@login_required
def profile(request):
    if request.user.role != 'student':
        return redirect('login')
    return render(request, 'users/profile.html')

@login_required
def edit_profile(request):
    if request.user.role != 'student':
        return redirect('login')
    if request.method == 'POST':
        user = request.user
        user.full_name = request.POST.get('full_name')
        user.bio = request.POST.get('bio')
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    return render(request, 'users/edit_profile.html')

@login_required
def teacher_announcements(request):
    if not request.user.is_teacher:
        return redirect('login')
    announcements = Announcement.objects.all().order_by('-created_at')
    return render(request, 'users/teacher_announcements.html', {
        'announcements': announcements,
        'global_announcements': announcements.filter(student=None),
        'student_specific_announcements': announcements.filter(student__isnull=False)
    })

@login_required
def teacher_results(request):
    if not request.user.is_teacher:
        return redirect('login')
    students = User.objects.filter(role='student')
    results = Result.objects.all().order_by('-created_at')
    return render(request, 'users/teacher_results.html', {
        'students': students,
        'results': results
    })

@login_required
def teacher_students(request):
    if not request.user.is_teacher:
        return redirect('login')
    students = User.objects.filter(role='student')
    return render(request, 'users/teacher_students.html', {'students': students})
