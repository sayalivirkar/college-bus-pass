from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django import forms
from .models import Student, Route, RoutePrice, BusPass


class StudentAdminForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    
    class Meta:
        model = Student
        fields = '__all__'
    
    def save(self, commit=True):
        student = super().save(commit=False)
        # Hash the password before saving
        if self.cleaned_data.get('password'):
            student.password = make_password(self.cleaned_data['password'])
        if commit:
            student.save()
        return student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    form = StudentAdminForm
    list_display = ['id', 'fullname', 'class_name', 'clgid', 'mobile', 'email', 'route1', 'created_at']
    list_filter = ['class_name', 'route1', 'created_at']
    search_fields = ['id', 'fullname', 'mobile', 'email', 'aadhar']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['id']
    list_per_page = 25
    
    # Show password field as password input in admin
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if 'password' in fields:
            fields = list(fields)
            fields.insert(fields.index('email'), 'password')
        return fields


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['name', 'source', 'destination', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'source', 'destination']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    list_per_page = 25


@admin.register(RoutePrice)
class RoutePriceAdmin(admin.ModelAdmin):
    list_display = ['route', 'month', 'price', 'created_at']
    list_filter = ['route', 'month', 'created_at']
    search_fields = ['route__name', 'route__source', 'route__destination', 'month']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['route', 'month']
    list_per_page = 25


@admin.register(BusPass)
class BusPassAdmin(admin.ModelAdmin):
    list_display = ['student', 'route', 'month', 'status', 'issue_date', 'expiry_date', 'created_at']
    list_filter = ['status', 'route', 'month', 'issue_date', 'created_at']
    search_fields = ['student__fullname', 'student__id', 'student__mobile', 'student__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'issue_date']
    ordering = ['-created_at']
    list_per_page = 25
    
    # Add custom actions
    actions = ['approve_selected', 'reject_selected']
    
    def approve_selected(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, "Selected bus passes have been approved.")
    
    def reject_selected(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, "Selected bus passes have been rejected.")
    
    approve_selected.short_description = "Approve selected bus passes"
    reject_selected.short_description = "Reject selected bus passes"

