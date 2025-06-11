from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

# Create your models here.

def user_profile_image_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/profile_images/<user_id>/<filename>
    return f'profile_images/{instance.id}/{filename}'

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, role=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        if not role:
            raise ValueError('Users must have a role')
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # Always set role to 'admin' and remove from extra_fields if present
        extra_fields.pop('role', None)
        return self.create_user(email, password, role='admin', **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('admin', 'Admin'),
    ]
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to=user_profile_image_path, null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def is_teacher(self):
        return self.role == 'teacher'

    @property
    def is_student(self):
        return self.role == 'student'

    def get_full_name(self):
        return self.full_name or self.email.split('@')[0]

    def get_role_display(self):
        return dict(self.ROLE_CHOICES).get(self.role, self.role)

class Announcement(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements_created')
    created_at = models.DateTimeField(default=timezone.now)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_active = models.BooleanField(default=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements', null=True, blank=True, 
                              help_text='If set, this announcement is only visible to this specific student')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.student:
            return f"{self.title} (For: {self.student.get_full_name()})"
        return self.title

    @property
    def is_student_specific(self):
        return self.student is not None

class Result(models.Model):
    GRADE_CHOICES = [
        ('A+', 'A+'),
        ('A', 'A'),
        ('B+', 'B+'),
        ('B', 'B'),
        ('C+', 'C+'),
        ('C', 'C'),
        ('D+', 'D+'),
        ('D', 'D'),
        ('F', 'F'),
    ]

    GRADE_RANGES = {
        'A+': (90, 100),
        'A': (80, 89.99),
        'B+': (70, 79.99),
        'B': (60, 69.99),
        'C+': (50, 59.99),
        'C': (40, 49.99),
        'D+': (35, 39.99),
        'D': (30, 34.99),
        'F': (0, 29.99),
    }

    PERFORMANCE_CHOICES = [
        ('excellent', 'Excellent'),
        ('very_good', 'Very Good'),
        ('good', 'Good'),
        ('satisfactory', 'Satisfactory'),
        ('needs_improvement', 'Needs Improvement'),
        ('poor', 'Poor'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='results')
    subject = models.CharField(max_length=100)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES)
    remarks = models.TextField(blank=True, null=True)
    overall_performance = models.CharField(max_length=20, choices=PERFORMANCE_CHOICES, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='results_created')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['student', 'subject']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.subject}"

    def percentage(self):
        """Calculate the percentage of marks obtained"""
        if self.total_marks == 0:
            return 0
        return (self.marks_obtained / self.total_marks) * 100

    def calculate_grade(self):
        """Calculate grade based on percentage"""
        percentage = self.percentage()
        for grade, (min_percent, max_percent) in self.GRADE_RANGES.items():
            if min_percent <= percentage <= max_percent:
                return grade
        return 'F'  # Default to F if no range matches

    def save(self, *args, **kwargs):
        """Override save to ensure grade matches percentage"""
        calculated_grade = self.calculate_grade()
        if self.grade != calculated_grade:
            self.grade = calculated_grade
        super().save(*args, **kwargs)

    def clean(self):
        """Validate the result data"""
        if self.marks_obtained > self.total_marks:
            raise ValidationError('Marks obtained cannot be greater than total marks')
        if self.marks_obtained < 0:
            raise ValidationError('Marks obtained cannot be negative')
        if self.total_marks <= 0:
            raise ValidationError('Total marks must be greater than zero')
