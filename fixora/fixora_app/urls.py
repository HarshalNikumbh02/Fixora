from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [

    # Core Public Interface Routes
    path('', views.home_page, name='home'), # LANDING HOME PAGE IS NOW AT THE ROOT URL '/'
    path('login/', views.login_page, name='login'), # SHIFTED LOGIN VIEW PATH TO Explicit '/login/'
    path('register/', views.register_page, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboards Management Scope paths
    path('dashboard/resident/', views.resident_dashboard, name='resident_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/worker/', views.worker_dashboard, name='worker_dashboard'),
    
    # Complaints Operations Routing Handlers
    path('complaints/log/', views.complaints_log_page, name='complaints_log'),
    path('complaint/new/', views.raise_complaint_form, name='raise_complaint'),
    path('complaint/raise/submit/', views.raise_complaint_submit, name='raise_complaint_submit'),
    
    # Service Booking Tracking
    path('service/book/', views.book_service_page, name='book_service'),
    path('service/book/submit/', views.book_service_submit, name='book_service_submit'),
    path('service/my/', views.my_services, name='my_services'),

    
    # Alerts
    path('alerts/', views.alerts, name='alerts'),

    #profile image upload
    path('profile/', views.profile, name='profile'),

    #manage User 
    path('dashboard/manage-users/', views.manage_users, name='manage_users'),

    #Admin complaint page
    path('manage-complaints/', views.manage_complaints, name='manage_complaints'),

    #update complaint status
    path('update-complaint/<int:complaint_id>/', views.update_complaint, name='update_complaint'),
    path('worker/update/<int:complaint_id>/', views.update_work_status, name='update_work_status'),
    path('worker/accept/<int:complaint_id>/', views.accept_complaint, name='accept_complaint'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('worker/service/accept/<int:service_id>/', views.accept_service, name='accept_service'),
    path('worker/service/update/<int:service_id>/', views.update_service_status, name='update_service_status'),
    
    #settings
    path('settings/',views.settings_page,name='settings'),
    path('change-password/',views.change_password,name='change_password'),
    path('send-password-otp/', views.send_password_otp, name='send_password_otp'),
    path('verify-password-otp/', views.verify_password_otp, name='verify_password_otp'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),

    # Superadmin Master Paths
    path('dashboard/superadmin/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('system/create-society/', views.create_society_and_admin, name='create_society_and_admin'),
    path('system/edit-admin/<int:society_id>/', views.edit_society_admin, name='edit_society_admin'),

    # Add these to your urlpatterns in urls.py
    path('settings/toggle-maintenance/', views.toggle_maintenance_mode, name='toggle_maintenance'),
    path('settings/download-logs/', views.download_error_logs, name='download_logs'),

    path('dashboard/analytics/', views.superadmin_analytics_view, name='superadmin_analytics'),
    path('api/analytics-data/', views.get_analytics_data, name='get_analytics_data'),
    path('manage/membership/<int:membership_id>/edit/', views.edit_membership, name='edit_membership'),
    path('manage/membership/<int:membership_id>/delete/', views.delete_membership, name='delete_membership'),

    #password reset
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='file/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='file/password_reset_complete.html'), name='password_reset_complete'),
]