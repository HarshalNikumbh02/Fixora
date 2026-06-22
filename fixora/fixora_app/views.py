from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib import messages
from django.core.cache import cache
from .models import User, Alert, Complaint, ServiceBooking, Society
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse
from django.db.models import Q, IntegerField, When, Case, Count
import random, os
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

def home_page(request):
    # This renders strictly the public informational landing dashboard page layout
    return render(request, 'file/home.html')

def login_page(request):

    if request.method == 'POST':

        username_val = request.POST.get('username')
        password_val = request.POST.get('password')

        user = authenticate(
            request,
            username=username_val,
            password=password_val
        )

        if user is not None:

            login(request, user)

            # SUPERADMIN - MASTER OF ALL DASHBOARDS
            if user.role == 'superadmin':
                return redirect('superadmin_dashboard')

            # ADMIN
            if user.role == 'admin':
                return redirect('admin_dashboard')

            # WORKER
            elif user.role == 'worker':
                return redirect('worker_dashboard')

            # RESIDENT
            else:
                return redirect('resident_dashboard')

        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')

    return render(request, 'file/login.html')

@login_required
def register_page(request):

    if request.user.role != 'admin':
        return redirect('resident_dashboard')

    if request.method == 'POST':

        # Strip whitespace to prevent accidental spaces ruining the data
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        role = request.POST.get('role')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # 1. Password Validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        # 2. Username Uniqueness
        if User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken. Please choose another.")
            return redirect('register')

        # 3. Email Format & Uniqueness
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email address already exists.")
            return redirect('register')

        # 4. Phone Number Format & Uniqueness
        if not phone.isdigit() or len(phone) != 10:
            messages.error(request, "Phone number must be exactly 10 digits.")
            return redirect('register')

        if User.objects.filter(phone=phone).exists():
            messages.error(request, "This phone number is already registered to another user.")
            return redirect('register')

        # Create user if all validations pass
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            phone=phone,
            society=request.user.society
        )

        user.save()

        messages.success(request, f"User {username} created successfully!")

        return redirect('manage_users')

    return render(request, 'file/register.html')

@login_required
def resident_dashboard(request):
    user_complaints = Complaint.objects.filter(
    resident__society=request.user.society
)
    search_query = request.GET.get('search')
    if search_query:
        user_complaints = user_complaints.filter(
            Q(title__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(status__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    user_complaints = user_complaints.order_by('-created_at')
    context = {
        'complaints': user_complaints
    }
    return render(request, 'file/resident_dashboard.html', context)

@login_required
def complaints_log_page(request):
    # This renders strictly your full history log dashboard list on sidebar click
    user_complaints = Complaint.objects.filter(
    resident__society=request.user.society).order_by('-created_at')
    context = {
        'complaints': user_complaints,
    }
    return render(request, 'file/complaints_log.html', context)

@login_required
def raise_complaint_form(request):
    # This renders exclusively your beautiful full-page form card layout block
    return render(request, 'file/raise_complaint.html')

@login_required
def admin_dashboard(request):

    residents_count = User.objects.filter(
        role='resident',
        society=request.user.society
    ).count()

    workers_count = User.objects.filter(
        role='worker',
        society=request.user.society
    ).count()

    complaints_count = Complaint.objects.filter(
        resident__society=request.user.society
    ).count()

    pending_count = Complaint.objects.filter(
        resident__society=request.user.society,
        status='pending'
    ).count()

    services_count = ServiceBooking.objects.filter(
        resident__society=request.user.society
    ).count()

    complaints = Complaint.objects.filter(
        resident__society=request.user.society
    ).order_by('-created_at')[:5]

    context = {
        'residents_count': residents_count,
        'workers_count': workers_count,
        'complaints_count': complaints_count,
        'pending_count': pending_count,
        'services_count': services_count,
        'complaints': complaints,
    }

    return render(request, 'file/admin_dashboard.html', context)

@login_required
def worker_dashboard(request):
    if request.user.role != 'worker':
        return redirect('resident_dashboard')

    # Fetch Unassigned Complaints for the Worker's Society
    available_complaints = Complaint.objects.filter(
        status='pending',
        assigned_worker__isnull=True,
        resident__society=request.user.society
    ).order_by('-created_at')

    # Fetch Complaints currently accepted/assigned to this Worker
    my_jobs = Complaint.objects.filter(
        assigned_worker=request.user
    ).order_by('-created_at')

    # Fetch Service Bookings
    available_services = ServiceBooking.objects.filter(
        status='pending',
        assigned_worker__isnull=True,
        resident__society=request.user.society
    ).order_by('-created_at')

    my_services = ServiceBooking.objects.filter(
        assigned_worker=request.user
    ).order_by('-created_at')

    context = {
        'available_complaints': available_complaints,
        'my_jobs': my_jobs,
        'available_services': available_services,  
        'my_services': my_services,                
    }

    return render(request, 'file/worker_dashboard.html', context)

@login_required
def accept_complaint(request, complaint_id):
    try:
        # Added security: Ensure the complaint belongs to the worker's society
        complaint = Complaint.objects.get(
            id=complaint_id, 
            resident__society=request.user.society
        )
    except Complaint.DoesNotExist:
        messages.error(request, "Complaint not found or unauthorized.")
        return redirect('worker_dashboard')

    if complaint.assigned_worker:
        messages.error(request, "This job has already been accepted.")
        return redirect('worker_dashboard')

    complaint.assigned_worker = request.user
    complaint.status = 'in_progress'
    complaint.save()

    messages.success(request, "Job accepted successfully.")
    return redirect('worker_dashboard')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def raise_complaint_submit(request):

    if request.method == 'POST':

        title = request.POST.get('title')
        category = request.POST.get('category')
        priority = request.POST.get('priority', 'low')
        description = request.POST.get('description')
        location = request.POST.get('location')
        uploaded_image = request.FILES.get('problem_image')
        if uploaded_image and uploaded_image.size > 5 * 1024 * 1024:
            messages.error(request, "File too large. Maximum size is 5MB.")
            return redirect('raise_complaint')

        if title and category:

            # Create Complaint
            complaint = Complaint.objects.create(
                resident=request.user,
                title=title,
                category=category,
                priority=priority,
                description=description,
                location=location,
                image=uploaded_image
            )

            # Create alerts for all admins if priority is HIGH
            if complaint.priority == 'high':

                admins = User.objects.filter(
                    role='admin',
                    society=complaint.resident.society
                )

                for admin in admins:

                    Alert.objects.create(
                        user=admin,
                        society=complaint.resident.society,
                        title="🚨 High Priority Complaint",
                        message=f"{complaint.title} requires urgent attention.",
                        alert_type='complaint'
                    )

            messages.success(
                request,
                "Complaint ticket submitted successfully!"
            )

            return redirect('resident_dashboard')

        messages.error(
            request,
            "Please fill out all required fields."
        )

        return redirect('raise_complaint')

    return redirect('raise_complaint')

@login_required
def book_service_page(request):
    # Renders your fresh new service layout wireframe structure
    return render(request, 'file/book_service.html')

@login_required
def book_service_submit(request):
    if request.method == 'POST':
        category = request.POST.get('category', 'plumbing')
        preferred_date = request.POST.get('preferred_date')
        preferred_time = request.POST.get('preferred_time_slot')
        location = request.POST.get('location')
        additional_notes = request.POST.get('additional_notes')
        uploaded_image = request.FILES.get('service_image')

        if preferred_date and preferred_time:
            ServiceBooking.objects.create(
                resident=request.user,
                category=category,
                preferred_date=preferred_date,
                preferred_time_slot=preferred_time,
                location=location,
                additional_notes=additional_notes,
                image=uploaded_image
            )
            messages.success(request, "Service booked successfully!")
            return redirect('resident_dashboard')

        messages.error(request, "Please fill out the required date and time slots.")
        return redirect('book_service')

    return redirect('book_service')

@login_required
def my_services(request):

    services = ServiceBooking.objects.filter(resident__society=request.user.society).order_by('-created_at')

    context = {
        'services': services
    }

    return render(request, 'file/my_services.html', context)

@login_required
def alerts(request):
    # 1. Only fetch alerts belonging specifically to this user
    alerts_data = Alert.objects.filter(user=request.user).order_by('-created_at')

    # 2. Mark all unread alerts as read since the user is now looking at them
    Alert.objects.filter(user=request.user, is_read=False).update(is_read=True)

    context = {
        'alerts_data': alerts_data
    }

    return render(request, 'file/alerts.html', context)

@login_required
def profile(request):

    if request.method == 'POST':

        user = request.user

        user.username = request.POST.get('username')
        user.email = request.POST.get('email')

        phone = request.POST.get('phone', '').strip()

        if (
            not phone.isdigit()
            or len(phone) != 10
            or phone.startswith('0')
        ):
            messages.error(
                request,
                "Phone number must be 10 digits and cannot start with 0."
            )
            return redirect('profile')

        user.phone = phone

        if request.FILES.get('profile_image'):
            user.profile_image = request.FILES.get('profile_image')

        user.save()

        messages.success(request, "Profile updated successfully.")

        # Redirect according to role
        if user.role == 'admin':
            return redirect('admin_dashboard')

        elif user.role == 'worker':
            return redirect('worker_dashboard')

        elif user.role == 'resident':
            return redirect('resident_dashboard')

        return redirect('profile')

    return render(request, 'file/profile.html')

@login_required
def manage_users(request):

    if request.user.role != 'admin':
        return redirect('resident_dashboard')

    residents = User.objects.filter(
        society=request.user.society,
        role='resident'
    )

    workers = User.objects.filter(
        society=request.user.society,
        role='worker'
    )

    context = {
        'residents': residents,
        'workers': workers,
    }

    return render(request, 'file/manage_users.html', context)

@login_required
def manage_complaints(request):

    if request.user.role != 'admin':
        return redirect('resident_dashboard')

    complaints = Complaint.objects.filter(
        resident__society=request.user.society
    ).order_by('-created_at')

    workers = User.objects.filter(
        role='worker',
        society=request.user.society
    )

    return render(
        request,
        'file/manage_complaints.html',
        {
            'complaints': complaints,
            'workers': workers
        }
    )

@login_required
def update_complaint(request, complaint_id):

    if request.user.role != 'admin':
        return redirect('resident_dashboard')

    complaint = Complaint.objects.get(
        id=complaint_id,
        resident__society=request.user.society
    )

    if request.method == 'POST':

        status = request.POST.get('status')
        worker_id = request.POST.get('worker')

        complaint.status = status

        if worker_id:
            worker = User.objects.get(id=worker_id)
            complaint.assigned_worker = worker

        complaint.save()

        messages.success(
            request,
            "Complaint updated successfully."
        )

    return redirect('manage_complaints')

@login_required
def update_work_status(request, complaint_id):

    if request.user.role != 'worker':
        return redirect('resident_dashboard')

    complaint = Complaint.objects.get(
        id=complaint_id,
        assigned_worker=request.user
    )

    if request.method == 'POST':

        complaint.status = request.POST.get('status')

        complaint.worker_notes = request.POST.get('worker_notes')

        if request.FILES.get('completion_image'):
            complaint.completion_image = request.FILES.get(
                'completion_image'
            )

        if complaint.status == 'completed':
            complaint.completed_at = timezone.now()

        complaint.save()

        messages.success(
            request,
            "Work status updated successfully."
        )

        return redirect('worker_dashboard')

    return redirect('worker_dashboard')

@login_required
def dashboard_redirect(request):
    # SUPERADMIN - MASTER OF ALL DASHBOARDS
    if request.user.role == 'superadmin':
        return redirect('superadmin_dashboard')
    if request.user.role == 'admin':
        return redirect('admin_dashboard')

    elif request.user.role == 'worker':
        return redirect('worker_dashboard')

    elif request.user.role == 'resident':
        return redirect('resident_dashboard')

    return redirect('login')

@login_required
def settings_page(request):
    # Check current status to pass to the template
    maintenance_active = cache.get('maintenance_mode', False)
    
    context = {
        'maintenance_active': maintenance_active
    }
    return render(request, 'file/settings.html', context)

@login_required
def change_password(request):

    if request.method == "POST":

        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return redirect('change_password')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('change_password')

        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return redirect('change_password')

        user.set_password(new_password)
        user.save()

        update_session_auth_hash(request, user)

        messages.success(request, "Password changed successfully.")

        return redirect('settings')

    return render(
        request,
        'file/change_password.html'
    )

def send_password_otp(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            otp = str(random.randint(100000, 999999))
            
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.save()

            send_mail(
                'Fixora Password Reset OTP',
                f'Your OTP is {otp}',
                None,
                [user.email]
            )
            
            # Store email in session to verify OTP later
            request.session['reset_email'] = email
            messages.success(request, "OTP sent to your email.")
            return redirect('verify_password_otp')
            
        except User.DoesNotExist:
            messages.error(request, "No account found with this email.")
            return redirect('send_password_otp')

    return render(request, 'file/send_password_otp.html') # You will need to create this simple HTML file with an email input

def verify_password_otp(request):
    email = request.session.get('reset_email')
    
    if not email:
        messages.error(request, "Session expired. Please request a new OTP.")
        return redirect('send_password_otp')

    if request.method == 'POST':
        otp = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = User.objects.get(email=email)

        if otp != user.otp:
            messages.error(request, "Invalid OTP.")
            return redirect('verify_password_otp')

        if timezone.now() > (user.otp_created_at + timedelta(seconds=60)):
            messages.error(request, "OTP expired.")
            return redirect('verify_password_otp')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('verify_password_otp')

        user.set_password(new_password)
        user.otp = None
        user.otp_created_at = None
        user.save()

        # Clear session
        del request.session['reset_email']
        
        messages.success(request, "Password reset successful. Please login.")
        return redirect('login') # Force them to login with new password

    return render(request, 'file/verify_password_otp.html')

@login_required
def superadmin_dashboard(request):
    # Security: Kick out anyone who isn't a superadmin
    if request.user.role != 'superadmin':
        return redirect('dashboard_redirect')

    from django.db.models import Count
    societies = Society.objects.annotate(
        total_users=Count('users')
    ).order_by('-created_at')

    # Fetch all admins and map them to their societies
    admins = User.objects.filter(role='admin').select_related('society')
    admin_dict = {admin.society_id: admin for admin in admins}

    # Dynamically attach the master admin to each society object
    for society in societies:
        society.master_admin = admin_dict.get(society.id)

    context = {
        'societies': societies,
    }
    return render(request, 'file/superadmin_dashboard.html', context)

@login_required
def edit_society_admin(request, society_id):
    if request.user.role != 'superadmin':
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        society = Society.objects.get(id=society_id)
        admin_user = User.objects.filter(role='admin', society=society).first()

        new_username = request.POST.get('admin_username').strip()
        new_email = request.POST.get('admin_email').strip()
        new_password = request.POST.get('admin_password')

        # 1. Validation: Check if the username is taken by someone else globally
        query = User.objects.filter(username=new_username)
        if admin_user:
            query = query.exclude(id=admin_user.id) # Ignore the current admin if we are just updating them
            
        if query.exists():
            messages.error(request, "That Admin username is already taken globally.")
            return redirect('superadmin_dashboard')

        # 2. Logic: Update existing OR Create new
        if admin_user:
            # UPDATE EXISTING ADMIN
            admin_user.username = new_username
            admin_user.email = new_email
            if new_password:
                admin_user.set_password(new_password)
            admin_user.save()
            messages.success(request, f"Admin credentials for '{society.name}' updated successfully.")
            
        else:
            # CREATE BRAND NEW ADMIN FOR "UNASSIGNED" SOCIETIES
            if not new_password:
                # If creating a new user from scratch, we absolutely need a password
                messages.error(request, f"You must provide a password to create a new admin for '{society.name}'.")
                return redirect('superadmin_dashboard')
                
            User.objects.create_user(
                username=new_username,
                email=new_email,
                password=new_password,
                role='admin',
                society=society
            )
            messages.success(request, f"New Master Admin created and assigned to '{society.name}'.")

    return redirect('superadmin_dashboard')

@login_required
def create_society_and_admin(request):
    if request.user.role != 'superadmin':
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        # Society Data
        society_name = request.POST.get('society_name')
        society_address = request.POST.get('society_address')
        
        # Admin Data
        admin_username = request.POST.get('admin_username').strip()
        admin_email = request.POST.get('admin_email').strip()
        admin_password = request.POST.get('admin_password')

        # 1. Validation Checks
        if User.objects.filter(username=admin_username).exists():
            messages.error(request, "That Admin username is already taken globally.")
            return redirect('superadmin_dashboard')

        # 2. Database Creation Transaction
        try:
            # Create the isolated Society bucket first
            new_society = Society.objects.create(
                name=society_name,
                address=society_address
            )

            # Create the master Admin and link them permanently to the new Society
            admin_user = User.objects.create_user(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                role='admin',
                society=new_society
            )

            messages.success(request, f"Platform Success: '{society_name}' initialized with master admin '{admin_username}'.")
        
        except Exception as e:
            messages.error(request, "A database error occurred during creation.")

    return redirect('superadmin_dashboard')

@login_required
def accept_service(request, service_id):
    if request.user.role != 'worker':
        return redirect('resident_dashboard')
        
    service = ServiceBooking.objects.get(id=service_id, resident__society=request.user.society)
    service.assigned_worker = request.user
    service.status = 'assigned'
    service.save()
    messages.success(request, "Service task accepted.")
    return redirect('worker_dashboard')

@login_required
def update_service_status(request, service_id):
    if request.user.role != 'worker':
        return redirect('resident_dashboard')
        
    service = ServiceBooking.objects.get(id=service_id, assigned_worker=request.user)
    if request.method == 'POST':
        service.status = request.POST.get('status')
        service.worker_notes = request.POST.get('worker_notes')
        
        if request.FILES.get('completion_image'):
            service.completion_image = request.FILES.get('completion_image')
            
        if service.status == 'completed':
            service.completed_at = timezone.now()
            
        service.save()
        messages.success(request, "Service status updated.")
        
    return redirect('worker_dashboard')

@login_required
def toggle_maintenance_mode(request):
    if request.user.role != 'superadmin':
        return redirect('dashboard_redirect')
    
    # Toggle the maintenance status in cache
    current_status = cache.get('maintenance_mode', False)
    cache.set('maintenance_mode', not current_status, timeout=None)
    
    status_text = "Enabled" if not current_status else "Disabled"
    messages.success(request, f"Maintenance mode has been {status_text}.")
    return redirect('settings')

@login_required
def download_error_logs(request):
    if request.user.role != 'superadmin':
        return redirect('dashboard_redirect')
        
    # Use the path defined in settings
    log_path = settings.LOG_FILE_PATH
    
    # Check if the file exists
    if os.path.exists(log_path):
        return FileResponse(open(log_path, 'rb'), as_attachment=True)
    else:
        # Create the file if it's missing, then inform the user
        with open(log_path, 'w') as f:
            f.write("System log initialized.")
        messages.warning(request, "Log file was missing; it has now been initialized. Please try downloading again.")
        return redirect('settings')
    
@login_required
def get_analytics_data(request):
    if request.user.role != 'superadmin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    # 1. Complaints by Category
    category_data = Complaint.objects.values('category').annotate(count=Count('id'))
    
    # 2. Daily Complaint Volume (Last 7 days)
    # This helps see if the platform usage is growing
    from datetime import timedelta
    from django.utils import timezone
    last_week = timezone.now() - timedelta(days=7)
    daily_data = Complaint.objects.filter(created_at__gte=last_week).values('created_at__date').annotate(count=Count('id'))

    return JsonResponse({
        'categories': list(category_data),
        'daily': list(daily_data)
    })

@login_required
def superadmin_analytics_view(request):
    if request.user.role != 'superadmin':
        return redirect('dashboard_redirect')
    return render(request, 'file/superadmin_analytics.html')