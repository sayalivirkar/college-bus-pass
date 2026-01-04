from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.utils import timezone
from datetime import date, datetime, timedelta
from .models import Student, Route, RoutePrice, BusPass, MultiSemesterBusPassApplication
from django.contrib.auth.models import User
import qrcode
from io import BytesIO
from django.core.files import File
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import os
from django.contrib.auth.hashers import make_password, check_password


def are_semesters_continuous(semesters_list):
    """Check if the selected semesters are continuous (e.g., Semester-1 and Semester-2, not Semester-1 and Semester-3)"""
    # Convert semester strings to numbers for comparison
    semester_numbers = []
    for sem in semesters_list:
        try:
            # Extract number from 'Semester-X'
            num = int(sem.split('-')[1])
            semester_numbers.append(num)
        except (IndexError, ValueError):
            return False
    
    # Sort the numbers
    semester_numbers.sort()
    
    # Check if they are consecutive
    for i in range(1, len(semester_numbers)):
        if semester_numbers[i] != semester_numbers[i-1] + 1:
            return False
    
    return True


def student_login(request):
    # Check if user is already logged in
    if request.session.get('student_logged_in'):
        student_id = request.session.get('student_id')
        if student_id:
            return redirect('student_dashboard')
    
    if request.method == 'POST':
        login_identifier = request.POST.get('login_identifier')  # This can be student_id, aadhar, mobile, or email
        password = request.POST.get('password')
        
        # Try to find the student using any of the possible login fields
        student = None
        try:
            # Check by student ID
            student = Student.objects.get(id=login_identifier)
        except Student.DoesNotExist:
            try:
                # Check by Aadhar
                student = Student.objects.get(aadhar=login_identifier)
            except Student.DoesNotExist:
                try:
                    # Check by Mobile
                    student = Student.objects.get(mobile=login_identifier)
                except Student.DoesNotExist:
                    try:
                        # Check by Email
                        student = Student.objects.get(email=login_identifier)
                    except Student.DoesNotExist:
                        pass
        
        if student and check_password(password, student.password):
            # Create a session for the student
            request.session['student_id'] = student.id
            request.session['student_logged_in'] = True
            messages.success(request, 'Login successful!')
            return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid credentials!')
    
    return render(request, 'buspass/login.html')

def student_dashboard(request):
    # Custom login check since we're using session-based auth for students
    if not request.session.get('student_logged_in'):
        messages.error(request, 'Please login first!')
        return redirect('student_login')
    
    student_id = request.session.get('student_id')
    if not student_id:
        messages.error(request, 'Please login first!')
        return redirect('student_login')
    
    student = get_object_or_404(Student, id=student_id)
    
    # Get student's bus passes
    bus_passes = BusPass.objects.filter(student=student)
    
    # Count passes by status
    total_passes = bus_passes.count()
    approved_passes = bus_passes.filter(status='approved').count()
    pending_passes = bus_passes.filter(status='pending').count()
    rejected_passes = bus_passes.filter(status='rejected').count()
    
    context = {
        'student': student,
        'bus_passes': bus_passes,
        'total_passes': total_passes,
        'approved_passes': approved_passes,
        'pending_passes': pending_passes,
        'rejected_passes': rejected_passes,
    }
    return render(request, 'buspass/student_dashboard.html', context)


def logout_view(request):
    request.session.flush()
    messages.success(request, 'You have been logged out successfully!')
    return redirect('student_login')


def apply_bus_pass(request):
    # Custom login check since we're using session-based auth for students
    if not request.session.get('student_logged_in'):
        messages.error(request, 'Please login first!')
        return redirect('student_login')
    
    student_id = request.session.get('student_id')
    if not student_id:
        messages.error(request, 'Please login first!')
        return redirect('student_login')
    
    student = get_object_or_404(Student, id=student_id)
    
    routes = Route.objects.filter(is_active=True)
    route_prices = RoutePrice.objects.filter(route__in=routes)
    
    if request.method == 'POST':
        route_id = request.POST.get('route')
        application_type = request.POST.get('application_type', 'single')
        
        route = get_object_or_404(Route, id=route_id)
        
        if application_type == 'single':
            # Single semester application
            semester = request.POST.get('semester')
            
            if not semester:
                messages.error(request, 'Please select a semester!')
                return redirect('apply_bus_pass')
            
            selected_semesters = [semester]
            
            # Get the price for this route and semester
            try:
                route_price = RoutePrice.objects.get(route=route, semester=semester)
                total_amount = float(route_price.price)
            except RoutePrice.DoesNotExist:
                messages.error(request, 'Price not found for selected route and semester!')
                return redirect('apply_bus_pass')
            
            # Calculate expiry date based on the semester
            year = date.today().year
            if semester == 'Semester-1':
                # Semester 1: Jan-June, expiry at end of June
                expiry_month = 6
                expiry_day = 30
            elif semester == 'Semester-2':
                # Semester 2: July-Dec, expiry at end of December
                expiry_month = 12
                expiry_day = 31
            elif semester == 'Semester-3':
                # For demonstration - could be different months
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
                # Default to current month
                expiry_month = date.today().month
                if expiry_month in [1, 3, 5, 7, 8, 10, 12]:
                    expiry_day = 31
                elif expiry_month in [4, 6, 9, 11]:
                    expiry_day = 30
                else:  # February
                    expiry_day = 29 if year % 4 == 0 else 28
            
            expiry_date = date(year, expiry_month, expiry_day)
            
            # Create the bus pass
            bus_pass = BusPass.objects.create(
                student=student,
                route=route,
                semester=semester,
                expiry_date=expiry_date,
                status='pending',
            )
            
            # Generate QR code
            qr_data = f"{bus_pass.id}|{student.id}|{student.fullname}|{route.name}|{semester}|{expiry_date}"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=4,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code to the bus pass model
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Create a filename for the QR code
            qr_filename = f'bus_pass_qr_{bus_pass.id}.png'
            bus_pass.qr_code.save(qr_filename, File(buffer), save=True)
            
            messages.success(request, f'Bus pass application submitted successfully for {semester}! Please upload payment receipt to complete the process.')
            return redirect('upload_payment_receipt', pass_id=bus_pass.id)
        else:
            # Multiple semester application
            selected_semesters = request.POST.getlist('semesters')
            
            if not selected_semesters:
                messages.error(request, 'Please select at least one semester!')
                return redirect('apply_bus_pass')
            
            # Validate that semesters are continuous
            if not are_semesters_continuous(selected_semesters):
                messages.error(request, 'Please select continuous semesters only! For example: Semester-1 and Semester-2, but not Semester-1 and Semester-3.')
                return redirect('apply_bus_pass')
            
            # Calculate total amount
            total_amount = 0
            for semester in selected_semesters:
                try:
                    route_price = RoutePrice.objects.get(route=route, semester=semester)
                    total_amount += float(route_price.price)
                except RoutePrice.DoesNotExist:
                    messages.error(request, f'Price not found for selected route and semester {semester}!')
                    return redirect('apply_bus_pass')
            
            # Create multi-semester application
            import json
            
            application = MultiSemesterBusPassApplication.objects.create(
                student=student,
                route=route,
                semesters=json.dumps(selected_semesters),
                total_amount=total_amount,
                status='pending',
            )
            
            messages.success(request, f'Multi-semester bus pass application submitted successfully for {len(selected_semesters)} semesters! Total amount: ₹{total_amount}. Please upload payment receipt to complete the process.')
            return redirect('upload_multi_semester_payment_receipt', application_id=application.id)
    
    context = {
        'student': student,
        'routes': routes,
        'route_prices': route_prices,
    }
    return render(request, 'buspass/apply_bus_pass.html', context)


def upload_payment_receipt(request, pass_id):
    # Custom login check since we're using session-based auth for students
    if not request.session.get('student_logged_in'):
        messages.error(request, 'Please login first!')
        return redirect('student_login')
    
    student_id = request.session.get('student_id')
    if not student_id:
        messages.error(request, 'Please login first!')
        return redirect('student_login')
    
    student = get_object_or_404(Student, id=student_id)
    bus_pass = get_object_or_404(BusPass, id=pass_id, student=student)
    
    if request.method == 'POST' and 'payment_receipt' in request.FILES:
        receipt = request.FILES['payment_receipt']
        
        # Validate file type
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
        ext = os.path.splitext(receipt.name)[1].lower()
        if ext not in allowed_extensions:
            messages.error(request, 'Invalid file type. Please upload JPG, PNG, or PDF files only.')
            return render(request, 'buspass/upload_receipt.html', {'bus_pass': bus_pass})
        
        bus_pass.payment_receipt = receipt
        bus_pass.save()
        
        messages.success(request, 'Payment receipt uploaded successfully! Your application is now pending for approval.')
        return redirect('student_dashboard')
    
    context = {
        'bus_pass': bus_pass,
    }
    return render(request, 'buspass/upload_receipt.html', context)


def upload_multi_semester_payment_receipt(request, application_id):
    # Custom login check since we're using session-based auth for students
    if not request.session.get('student_logged_in'):
        messages.error(request, 'Please login first!')
        return redirect('student_login')
    
    student_id = request.session.get('student_id')
    if not student_id:
        messages.error(request, 'Please login first!')
        return redirect('student_login')
    
    student = get_object_or_404(Student, id=student_id)
    application = get_object_or_404(MultiSemesterBusPassApplication, id=application_id, student=student)
    
    if request.method == 'POST' and 'payment_receipt' in request.FILES:
        receipt = request.FILES['payment_receipt']
        
        # Validate file type
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
        ext = os.path.splitext(receipt.name)[1].lower()
        if ext not in allowed_extensions:
            messages.error(request, 'Invalid file type. Please upload JPG, PNG, or PDF files only.')
            return render(request, 'buspass/upload_receipt.html', {'application': application})
        
        application.payment_receipt = receipt
        application.save()
        
        messages.success(request, 'Payment receipt uploaded successfully! Your multi-semester application is now pending for approval.')
        return redirect('student_dashboard')
    
    context = {
        'application': application,
    }
    return render(request, 'buspass/upload_multi_semester_receipt.html', context)


def download_bus_pass(request, pass_id):
    # Custom login check since we're using session-based auth for students
    if not request.session.get('student_logged_in'):
        messages.error(request, 'Please login first!')
        return redirect('student_login')
    
    student_id = request.session.get('student_id')
    if not student_id:
        messages.error(request, 'Please login first!')
        return redirect('student_login')
    
    student = get_object_or_404(Student, id=student_id)
    bus_pass = get_object_or_404(BusPass, id=pass_id, student=student)
    
    if bus_pass.status != 'approved':
        messages.error(request, 'Bus pass is not approved yet!')
        return redirect('student_dashboard')
    
    # Create PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width/2.0, height - 100, "COLLEGE BUS PASS")
    
    # Student Information
    p.setFont("Helvetica", 12)
    y_position = height - 140
    p.drawString(100, y_position, f"Student Name: {bus_pass.student.fullname}")
    y_position -= 20
    p.drawString(100, y_position, f"Student ID: {bus_pass.student.id}")
    y_position -= 20
    p.drawString(100, y_position, f"Class: {bus_pass.student.class_name}")
    y_position -= 20
    p.drawString(100, y_position, f"College ID: {bus_pass.student.clgid}")
    y_position -= 20
    p.drawString(100, y_position, f"Mobile: {bus_pass.student.mobile}")
    y_position -= 20
    p.drawString(100, y_position, f"Email: {bus_pass.student.email}")
    y_position -= 30
    
    # Route Information
    p.drawString(100, y_position, f"Route: {bus_pass.route.source} → {bus_pass.route.destination}")
    y_position -= 20
    p.drawString(100, y_position, f"Semester: {bus_pass.semester}")
    y_position -= 20
    p.drawString(100, y_position, f"Driver Name: {bus_pass.route.driver_name}")
    y_position -= 20
    p.drawString(100, y_position, f"Driver Contact: {bus_pass.route.driver_contact}")
    y_position -= 20
    p.drawString(100, y_position, f"Arrival at Source: {bus_pass.route.arrival_time_at_source.strftime('%H:%M')}")
    y_position -= 20
    p.drawString(100, y_position, f"Arrival at Destination: {bus_pass.route.arrival_time_at_destination.strftime('%H:%M')}")
    y_position -= 20
    p.drawString(100, y_position, f"Issue Date: {bus_pass.issue_date.strftime('%d %B, %Y')}")
    y_position -= 20
    p.drawString(100, y_position, f"Expiry Date: {bus_pass.expiry_date.strftime('%d %B, %Y')}")
    y_position -= 40
    
    # QR Code
    if bus_pass.qr_code:
        qr_path = os.path.join(settings.MEDIA_ROOT, str(bus_pass.qr_code))
        if os.path.exists(qr_path):
            p.drawInlineImage(qr_path, width/2.0 - 50, y_position - 100, 100, 100)
    
    y_position -= 120
    p.drawString(100, y_position, "Valid only with original ID proof")
    
    # Footer
    p.setFont("Helvetica-Oblique", 10)
    p.drawCentredString(width/2.0, 50, "This is a computer-generated pass and does not require a signature.")
    
    p.showPage()
    p.save()
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bus_pass_{bus_pass.id}.pdf"'
    response.write(pdf)
    
    return response




def home(request):
    # If user is already logged in, redirect to dashboard
    if request.session.get('student_logged_in'):
        return redirect('student_dashboard')
    return render(request, 'buspass/home.html')


def admin_reports(request):
    # This view would be for admin reports (to be implemented)
    return render(request, 'buspass/admin_reports.html')

