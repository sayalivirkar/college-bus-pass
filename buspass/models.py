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
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.source} → {self.destination} ({self.name})"

    class Meta:
        ordering = ['name']


class RoutePrice(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='prices')
    month = models.CharField(max_length=20)  # e.g., "January", "February", etc.
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.route.name} - {self.month}: ₹{self.price}"

    class Meta:
        unique_together = ['route', 'month']
        ordering = ['route', 'month']


def upload_pass_receipt_path(instance, filename):
    # Upload path: receipts/student_id/pass_id/filename
    return f'receipts/{instance.student.id}/{instance.id}/{filename}'

class BusPass(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='bus_passes')
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    month = models.CharField(max_length=20)
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
        return f"{self.student.fullname} - {self.route.name} - {self.month}"

    class Meta:
        ordering = ['-created_at']

