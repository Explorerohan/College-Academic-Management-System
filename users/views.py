from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .models import User, Announcement, Result
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.core.exceptions import ValidationError

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
        try:
            subject = request.POST.get('subject')
            marks = float(request.POST.get('marks', 0))
            total_marks = float(request.POST.get('total_marks', 100))
            remarks = request.POST.get('remarks')
            overall_performance = request.POST.get('overall_performance')
            send_email = request.POST.get('send_email') == 'on'
            
            # Create a temporary result object to calculate grade
            temp_result = Result(
                student=student,
                subject=subject,
                marks_obtained=marks,
                total_marks=total_marks,
                remarks=remarks,
                overall_performance=overall_performance,
                created_by=request.user
            )
            
            # Validate the result
            temp_result.clean()
            
            # Calculate grade based on percentage
            grade = temp_result.calculate_grade()
            
            # Check if result already exists for this subject
            existing_result = Result.objects.filter(student=student, subject=subject).first()
            
            if existing_result:
                # Update existing result
                existing_result.marks_obtained = marks
                existing_result.total_marks = total_marks
                existing_result.grade = grade
                existing_result.remarks = remarks
                existing_result.overall_performance = overall_performance
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
                    overall_performance=overall_performance,
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
                    Percentage: {result.percentage():.2f}%
                    Grade: {grade}
                    Overall Performance: {result.get_overall_performance_display() or 'Not specified'}
                    
                    Remarks: {remarks or 'No remarks'}
                    
                    This is an automated message from the Academic Management System.
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[student.email],
                    fail_silently=True,
                )
            
            messages.success(request, 'Result saved successfully!')
            return redirect('teacher_student_detail', student_id=student.id)
            
        except ValidationError as e:
            messages.error(request, str(e))
        except ValueError:
            messages.error(request, 'Invalid marks entered. Please enter valid numbers.')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
    
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
    context = {
        'results': results,
        'grade_ranges': Result.GRADE_RANGES
    }
    return render(request, 'users/results.html', context)

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

@login_required
def teacher_edit_result(request, result_id):
    if not request.user.is_teacher:
        return redirect('login')
    
    result = get_object_or_404(Result, id=result_id)
    student = result.student
    
    if request.method == 'POST':
        try:
            subject = request.POST.get('subject')
            marks = float(request.POST.get('marks', 0))
            total_marks = float(request.POST.get('total_marks', 100))
            remarks = request.POST.get('remarks')
            overall_performance = request.POST.get('overall_performance')
            send_email = request.POST.get('send_email') == 'on'
            
            # Create a temporary result object to calculate grade
            temp_result = Result(
                student=student,
                subject=subject,
                marks_obtained=marks,
                total_marks=total_marks,
                remarks=remarks,
                overall_performance=overall_performance,
                created_by=request.user
            )
            
            # Validate the result
            temp_result.clean()
            
            # Calculate grade based on percentage
            grade = temp_result.calculate_grade()
            
            # Update the result
            result.subject = subject
            result.marks_obtained = marks
            result.total_marks = total_marks
            result.grade = grade
            result.remarks = remarks
            result.overall_performance = overall_performance
            result.save()
            
            if send_email:
                # Send email to student
                send_mail(
                    subject=f'Result Updated: {subject}',
                    message=f'''
                    Dear {student.get_full_name()},
                    
                    Your result for {subject} has been updated:
                    
                    Marks Obtained: {marks}/{total_marks}
                    Percentage: {result.percentage():.2f}%
                    Grade: {grade}
                    Overall Performance: {result.get_overall_performance_display() or 'Not specified'}
                    
                    Remarks: {remarks or 'No remarks'}
                    
                    This is an automated message from the Academic Management System.
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[student.email],
                    fail_silently=True,
                )
            
            messages.success(request, 'Result updated successfully!')
            return redirect('teacher_results')
            
        except ValidationError as e:
            messages.error(request, str(e))
        except ValueError:
            messages.error(request, 'Invalid marks entered. Please enter valid numbers.')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
    
    context = {
        'student': student,
        'result': result,
        'is_edit': True
    }
    return render(request, 'users/teacher_add_result.html', context)

@login_required
def teacher_delete_result(request, result_id):
    if not request.user.is_teacher:
        messages.error(request, 'You do not have permission to delete results.')
        return redirect('login')
    
    try:
        result = get_object_or_404(Result, id=result_id)
        
        if request.method == 'POST':
            student_name = result.student.get_full_name()
            subject = result.subject
            result.delete()
            messages.success(request, f'Result for {student_name} in {subject} has been deleted successfully!')
        else:
            messages.error(request, 'Invalid request method. Please use the delete button.')
            
    except Result.DoesNotExist:
        messages.error(request, 'The result you are trying to delete does not exist.')
    except Exception as e:
        messages.error(request, f'An error occurred while deleting the result: {str(e)}')
    
    return redirect('teacher_results')
