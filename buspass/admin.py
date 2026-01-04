import json
from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django import forms
from .models import Student, Route, RoutePrice, BusPass, MultiSemesterBusPassApplication


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
    list_display = ['name', 'source', 'destination', 'driver_name', 'driver_contact', 'arrival_time_at_source', 'arrival_time_at_destination', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'source', 'destination', 'driver_name', 'driver_contact']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    list_per_page = 25
    
    fieldsets = (
        ('Route Information', {
            'fields': ('name', 'source', 'destination', 'is_active')
        }),
        ('Driver Information', {
            'fields': ('driver_name', 'driver_contact')
        }),
        ('Schedule Information', {
            'fields': ('arrival_time_at_source', 'arrival_time_at_destination')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RoutePrice)
class RoutePriceAdmin(admin.ModelAdmin):
    list_display = ['route', 'semester', 'price', 'created_at']
    list_filter = ['route', 'semester', 'created_at']
    search_fields = ['route__name', 'route__source', 'route__destination', 'semester']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['route', 'semester']
    list_per_page = 25


@admin.register(BusPass)
class BusPassAdmin(admin.ModelAdmin):
    list_display = ['student', 'route', 'semester', 'status', 'issue_date', 'expiry_date', 'created_at']
    list_filter = ['status', 'route', 'semester', 'issue_date', 'created_at']
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


@admin.register(MultiSemesterBusPassApplication)
class MultiSemesterBusPassApplicationAdmin(admin.ModelAdmin):
    list_display = ['student', 'route', 'get_semesters_display', 'total_amount', 'status', 'issue_date', 'created_at']
    list_filter = ['status', 'route', 'issue_date', 'created_at']
    search_fields = ['student__fullname', 'student__id', 'student__mobile', 'student__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'issue_date']
    ordering = ['-created_at']
    list_per_page = 25
    
    # Add custom actions
    actions = ['approve_selected', 'reject_selected']
    
    def get_semesters_display(self, obj):
        try:
            semesters_list = json.loads(obj.semesters)
            return ", ".join(semesters_list)
        except (json.JSONDecodeError, TypeError):
            return obj.semesters
    get_semesters_display.short_description = "Semesters"
    
    def approve_selected(self, request, queryset):
        for application in queryset:
            application.status = 'approved'
            application.save()
            # Create individual BusPass records for each semester
            try:
                semesters_list = json.loads(application.semesters)
            except json.JSONDecodeError:
                semesters_list = []
            
            for semester in semesters_list:
                # Get the route price for this semester
                route_price = RoutePrice.objects.get(route=application.route, semester=semester)
                
                # Calculate expiry date based on semester
                from datetime import date
                year = date.today().year
                if semester == 'Semester-1':
                    expiry_month = 6
                    expiry_day = 30
                elif semester == 'Semester-2':
                    expiry_month = 12
                    expiry_day = 31
                elif semester == 'Semester-3':
                    expiry_month = 6
                    expiry_day = 30
                elif semester == 'Semester-4':
                    expiry_month = 12
                    expiry_day = 31
                elif semester == 'Semester-5':
                    expiry_month = 6
                    expiry_day = 30
                elif semester == 'Semester-6':
                    expiry_month = 12
                    expiry_day = 31
                else:
                    expiry_month = 12
                    expiry_day = 31
                
                expiry_date = date(year, expiry_month, expiry_day)
                
                # Create individual bus pass
                BusPass.objects.create(
                    student=application.student,
                    route=application.route,
                    semester=semester,
                    issue_date=application.issue_date,
                    expiry_date=expiry_date,
                    status='approved',
                    payment_receipt=application.payment_receipt,
                    approved_by=request.user,
                    approved_at=application.approved_at or application.created_at,
                )
        self.message_user(request, f"{queryset.count()} multi-semester applications have been approved and individual bus passes created.")
    
    def reject_selected(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} multi-semester applications have been rejected.")
    
    approve_selected.short_description = "Approve selected multi-semester applications and create individual passes"
    reject_selected.short_description = "Reject selected multi-semester applications"

