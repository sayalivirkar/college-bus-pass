# College Bus Pass Management System

A Django-based application for managing college bus passes with student and admin panels.

## Features

### Admin Panel (Django Admin)
- Student management (CRUD operations)
- Route management (Source, Destination, Active/Inactive)
- Route pricing management
- Bus pass approval/rejection
- Reports and analytics (Weekly, Monthly, Quarterly, Yearly)
- PDF and Excel export capabilities

### Student Panel
- Multiple login options (Student ID, Aadhar, Mobile, Email)
- Apply for bus passes
- Upload payment receipts
- Download approved bus passes (with QR codes)
- View pass status and history

## Technology Stack

- **Backend**: Django 4.x
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Database**: SQLite (default), can be changed to PostgreSQL/MySQL
- **File Handling**: Django file uploads
- **QR Code Generation**: Python qrcode library
- **PDF Generation**: ReportLab
- **Authentication**: Django built-in auth system

## Setup Instructions

1. **Clone the repository** (or extract the project files)

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**:
   ```bash
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   pip install django djangorestframework pillow qrcode reportlab
   ```

5. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Create sample data** (optional):
   ```bash
   python manage.py create_sample_data
   ```

8. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

## Usage

### Admin Panel
- Access at: `http://127.0.0.1:8000/admin/`
- Use the superuser credentials created in step 6

### Student Panel
- Access at: `http://127.0.0.1:8000/`
- Login with student credentials (ID, Aadhar, Mobile, or Email + password)

## Project Structure

```
college-bus-pass/
├── buspass_project/          # Django project settings
├── buspass/                  # Main application
│   ├── migrations/           # Database migrations
│   ├── templates/buspass/    # HTML templates
│   ├── management/commands/  # Custom management commands
│   ├── models.py             # Database models
│   ├── views.py              # View functions
│   ├── urls.py               # URL patterns
│   └── admin.py              # Admin configuration
├── static/                   # Static files (CSS, JS, Images)
├── media/                    # User uploaded files
├── templates/                # Base templates
├── manage.py                 # Django management utility
├── requirements.txt          # Project dependencies
└── README.md                 # This file
```

## Key Models

1. **Student**: Student information (ID, name, class, contact details, etc.)
2. **Route**: Bus routes (source, destination, active status)
3. **RoutePrice**: Pricing for routes per month
4. **BusPass**: Bus pass applications with status (pending/approved/rejected)

## Security Features

- Password hashing using Django's built-in hasher
- CSRF protection
- File upload validation
- SQL injection prevention through ORM
- XSS protection through template escaping

## Custom Management Commands

- `create_sample_data`: Creates sample routes, students, and bus passes for testing

## API Endpoints

- `/` - Home page
- `/login/` - Student login
- `/dashboard/` - Student dashboard
- `/apply/` - Apply for bus pass
- `/upload_receipt/<uuid:pass_id>/` - Upload payment receipt
- `/download_pass/<uuid:pass_id>/` - Download bus pass PDF
- `/logout/` - Logout
- `/admin/` - Admin panel

## Admin Features

- Enhanced admin interface with search, filters, and pagination
- Bulk actions for approving/rejecting bus passes
- Detailed views for all models
- Custom admin actions

## Student Features

- Responsive UI with Bootstrap 5
- Status badges for pass applications
- QR code generation for bus passes
- PDF download functionality
- Session-based authentication

## Future Enhancements

- Email notifications for pass approval/rejection
- SMS notifications
- QR code scanning for pass verification
- Analytics dashboard with charts
- Mobile app integration
- Payment gateway integration
- Route optimization algorithms