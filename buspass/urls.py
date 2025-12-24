from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.student_login, name='student_login'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('apply/', views.apply_bus_pass, name='apply_bus_pass'),
    path('upload_receipt/<uuid:pass_id>/', views.upload_payment_receipt, name='upload_payment_receipt'),
    path('download_pass/<uuid:pass_id>/', views.download_bus_pass, name='download_bus_pass'),
    path('logout/', views.logout_view, name='logout'),
    path('admin_reports/', views.admin_reports, name='admin_reports'),
]