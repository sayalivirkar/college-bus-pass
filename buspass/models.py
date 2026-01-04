from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from datetime import date
import uuid
import os


class Student(models.Model):
    id = models.CharField(max_length=10, unique=True, primary_key=True)
    fullname = models.CharField(max_length=200)
    class_name = models.CharField(max_length=10, verbose_name="Class")
    clgid = models.IntegerField(verbose_name="College ID")
    address = models.TextField()
    route1 = models.CharField(max_length=100, verbose_name="Route")
    date_of_birth = models.DateField()
    aadhar = models.CharField(max_length=12, unique=True, validators=[
        RegexValidator(regex=r'^\d{12}$', message="Aadhar number must be 12 digits")
    ])
    mobile = models.CharField(max_length=10, unique=True, validators=[
        RegexValidator(regex=r'^\d{10}$', message="Mobile number must be 10 digits")
    ])
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # This will be hashed
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.fullname} ({self.id})"

    class Meta:
        ordering = ['id']


class Route(models.Model):
    name = models.CharField(max_length=100, unique=True)
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    driver_name = models.CharField(max_length=100, verbose_name="Driver Name", default="TBD")
    driver_contact = models.CharField(max_length=15, verbose_name="Driver Contact Number", validators=[
        RegexValidator(regex=r'^\d{10,15}$', message="Driver contact number must be 10 to 15 digits")
    ], default="0000000000")
    arrival_time_at_source = models.TimeField(verbose_name="Arrival Time at Source", default="08:00")
    arrival_time_at_destination = models.TimeField(verbose_name="Arrival Time at Destination", default="09:00")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.source} → {self.destination} ({self.name})"

    class Meta:
        ordering = ['name']


class RoutePrice(models.Model):
    SEMESTER_CHOICES = [
        ('Semester-1', 'Semester-1'),
        ('Semester-2', 'Semester-2'),
        ('Semester-3', 'Semester-3'),
        ('Semester-4', 'Semester-4'),
        ('Semester-5', 'Semester-5'),
        ('Semester-6', 'Semester-6'),
    ]
    
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='prices')
    semester = models.CharField(max_length=20, choices=SEMESTER_CHOICES)  # e.g., "Semester-1", "Semester-2", etc.
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.route.name} - {self.semester}: ₹{self.price}"

    class Meta:
        unique_together = ['route', 'semester']
        ordering = ['route', 'semester']


def upload_pass_receipt_path(instance, filename):
    # Upload path: receipts/student_id/pass_id/filename
    return f'receipts/{instance.student.id}/{instance.id}/{filename}'

class MultiSemesterBusPassApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='multi_semester_applications')
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    semesters = models.TextField(help_text="List of continuous semesters selected, stored as JSON string")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total amount for all semesters")
    issue_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_receipt = models.FileField(upload_to=upload_pass_receipt_path, null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_multi_semester_passes')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rejected_multi_semester_passes')
    rejected_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.fullname} - {self.route.name} - {len(self.semesters)} semesters"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Multi-Semester Bus Pass Application"
        verbose_name_plural = "Multi-Semester Bus Pass Applications"


class BusPass(models.Model):
    SEMESTER_CHOICES = [
        ('Semester-1', 'Semester-1'),
        ('Semester-2', 'Semester-2'),
        ('Semester-3', 'Semester-3'),
        ('Semester-4', 'Semester-4'),
        ('Semester-5', 'Semester-5'),
        ('Semester-6', 'Semester-6'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='bus_passes')
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    semester = models.CharField(max_length=20, choices=SEMESTER_CHOICES)
    issue_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_receipt = models.FileField(upload_to=upload_pass_receipt_path, null=True, blank=True)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_passes')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rejected_passes')
    rejected_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.fullname} - {self.route.name} - {self.semester}"

    class Meta:
        ordering = ['-created_at']

