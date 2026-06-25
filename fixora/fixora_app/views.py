from urllib import request
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib import messages
from django.core.cache import cache
from .models import User, Alert, Complaint, ServiceBooking, Society, SocietyMembership
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse
from django.db.models import Q, IntegerField, When, Case, Count
import random, os
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404

def home_page(request):
    # This renders strictly the public informational landing dashboard page layout
    return render(request, 'file/home.html')

def login_page(request):
    if request.method == 'POST':
        login_id = request.POST.get('login_id', '').strip()
        password_val = request.POST.get('password')

        # 1. STRICT SEARCH: Only check Email OR Phone (Username is ignored)
        matching_users = User.objects.filter(
            Q(email__iexact=login_id) | 
            Q(phone=login_id)
        )

        user = None
        for account in matching_users:
            # We still pass account.username to authenticate() because Django requires it internally, 
            # but the user typed their email/phone to get here.
            user = authenticate(request, username=account.username, password=password_val)
            if user is not None:
                break 

        if user is not None:
            login(request, user)
            if user.role == 'superadmin':
                return redirect('superadmin_dashboard')
            elif user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'worker':
                return redirect('worker_dashboard')
            else:
                return redirect('resident_dashboard')
        else:
            messages.error(request, "Invalid Email/Phone or Password. Please try again.")
            return redirect('login')

    return render(request, 'file/login.html')

@login_required
def register_page(request):
    if request.user.role != 'admin':
        return redirect('resident_dashboard')

    if request.method == 'POST':
        # Capture Full Name instead of username
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        role = request.POST.get('role')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        flat_number = request.POST.get('flat_number', '').strip()
        worker_id = request.POST.get('worker_id', '').strip()

        # Smart Lookup by Email OR Phone
        query = Q(email__iexact=email)
        if phone and len(phone) == 10:
            query |= Q(phone=phone)
            
        existing_user = User.objects.filter(query).first()

        if existing_user:
            # Link existing user without touching password
            if role == 'resident' and SocietyMembership.objects.filter(user=existing_user, society=request.user.society, flat_number=flat_number).exists():
                messages.error(request, f"This account is already registered in Flat {flat_number}.")
                return redirect('register')
                
            if role == 'worker' and SocietyMembership.objects.filter(user=existing_user, society=request.user.society, worker_id=worker_id).exists():
                messages.error(request, f"This account is already registered as Worker {worker_id}.")
                return redirect('register')
            
            SocietyMembership.objects.create(
                user=existing_user,
                society=request.user.society,
                flat_number=flat_number if role == 'resident' else None,
                worker_id=worker_id if role == 'worker' else None,
                role=role
            )
            messages.success(request, f"Account '{existing_user.first_name}' successfully linked to the society!")
            return redirect('manage_users')

        # Create New User Validations
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        if not phone.isdigit() or len(phone) != 10:
            messages.error(request, "Phone number must be exactly 10 digits.")
            return redirect('register')

        if User.objects.filter(phone=phone).exists():
            messages.error(request, "This phone number is already registered.")
            return redirect('register')

        # Create the Global User using Email as the internal username, and Full Name in first_name
        user = User.objects.create_user(
            username=email,          # Secretly mapping username to email to satisfy Django's core
            email=email,
            password=password,
            first_name=full_name,    # Storing their actual Full Name here!
            role=role,
            phone=phone,
            society=request.user.society
        )
        user.save()

        wing = request.POST.get('wing', '').strip().upper() # .upper() makes 'a' turn into 'A' uniformly!
        flat_number = request.POST.get('flat_number', '').strip()
        SocietyMembership.objects.create(
            user=user,
            society=request.user.society,
            wing=wing if role == 'resident' else None,
            flat_number=flat_number if role == 'resident' else None,
            worker_id=worker_id if role == 'worker' else None,
            role=role
        )

        messages.success(request, f"New {role} created successfully!")
        return redirect('manage_users')

    return render(request, 'file/register.html')

@login_required
def resident_dashboard(request):
    user_complaints = Complaint.objects.filter(resident=request.user)
    search_query = request.GET.get('search')
    if search_query:
        user_complaints = user_complaints.filter(
            Q(title__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(status__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    user_complaints = user_complaints.order_by('-created_at')
    memberships = SocietyMembership.objects.filter(user=request.user, role='resident')
    context = {
        'complaints': user_complaints,
        'memberships': memberships
    }
    return render(request, 'file/resident_dashboard.html', context)

@login_required
def complaints_log_page(request):
    # Show complaints across all flats
    user_complaints = Complaint.objects.filter(resident=request.user).order_by('-created_at')
    return render(request, 'file/complaints_log.html', {'complaints': user_complaints})

@login_required
def raise_complaint_form(request):
    # Pass flats to the complaint form so they can select one
    memberships = SocietyMembership.objects.filter(user=request.user, role='resident')
    return render(request, 'file/raise_complaint.html', {'memberships': memberships})

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
    # Pass flats to the service form so they can select one
    memberships = SocietyMembership.objects.filter(user=request.user, role='resident')
    return render(request, 'file/book_service.html', {'memberships': memberships})

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
    # Show services across all flats
    services = ServiceBooking.objects.filter(resident=request.user).order_by('-created_at')
    return render(request, 'file/my_services.html', {'services': services})

@login_required
def alerts(request):
    # 1. Fetch all alerts for this user, newest first
    user_alerts = Alert.objects.filter(user=request.user).order_by('-created_at')
    
    # 2. Mark them all as read the moment they open this page!
    Alert.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    context = {
        'alerts': user_alerts
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
    selected_wing = request.GET.get('wing', '')
    residents = SocietyMembership.objects.filter(society=request.user.society, role='resident')
    active_wings = residents.exclude(wing__isnull=True).exclude(wing__exact='').values_list('wing', flat=True).distinct().order_by('wing')
    if selected_wing:
        residents = residents.filter(wing=selected_wing)
    workers = SocietyMembership.objects.filter(society=request.user.society, role='worker')
    context = {
        'residents': residents,
        'active_wings': active_wings,
        'selected_wing': selected_wing,
        'workers': workers, # <--- Added workers to the context!
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

@login_required
def edit_membership(request, membership_id):
    # Fetch the exact membership record
    membership = get_object_or_404(SocietyMembership, id=membership_id, society=request.user.society)
    
    if request.method == 'POST':
        # Update flat number
        new_flat = request.POST.get('flat_number')
        if new_flat is not None: # Changed to 'is not None' so it can accept empty strings if needed
            membership.flat_number = new_flat
            
        wing = request.POST.get('wing', '').strip().upper() 
        flat_number = request.POST.get('flat_number', '').strip()
            
            # 2. Assign it to the membership object:
        membership.wing = wing if wing else None
        membership.flat_number = flat_number
            

        # Update worker ID
        new_worker_id = request.POST.get('worker_id')
        if new_worker_id is not None:
            membership.worker_id = new_worker_id
            
        membership.save()
            
        # Update user details (Name/Phone)
        # Note: Because this updates the Global User, it updates their name everywhere.
        user = membership.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.save()

        messages.success(request, "Resident details updated successfully.")
        return redirect('manage_users') # Change to your actual user list URL

    # If GET request, render the edit form (you'll need to create this simple HTML form)
    return render(request, 'file/edit_membership.html', {'membership': membership})


@login_required
def delete_membership(request, membership_id):
    if request.method == 'POST':
        membership = get_object_or_404(SocietyMembership, id=membership_id, society=request.user.society)
        
        # We delete the MEMBERSHIP, not the User.
        membership.delete()
        
        messages.success(request, "Resident has been removed from your society.")
        return redirect('manage_users')
    
def forgot_password(request):
    if request.method == 'POST':
        # Check which form they submitted using a hidden input field we will add to the HTML
        reset_method = request.POST.get('reset_method') 
        
        # ==========================================
        # SCENARIO 1: THEY CHOSE PHONE OTP
        # ==========================================
        if reset_method == 'phone':
            phone = request.POST.get('phone')
            try:
                user = User.objects.get(phone=phone) 
                otp = str(random.randint(100000, 999999))
                
                request.session['reset_phone'] = phone
                request.session['reset_otp'] = otp
                
                # Mock SMS output to your terminal
                print("\n" + "="*30)
                print(f"📱 MOCK SMS TO: {phone}")
                print(f"🔑 YOUR FIXORA OTP IS: {otp}")
                print("="*30 + "\n")
                
                messages.success(request, 'OTP sent successfully! Please check your phone.')
                return redirect('verify_otp')
                
            except User.DoesNotExist:
                messages.error(request, 'No account found with this phone number.')
                
       # ==========================================
        # SCENARIO 2: THEY CHOSE EMAIL
        # ==========================================
        elif reset_method == 'email':
            email = request.POST.get('email')
            try:
                user = User.objects.get(email=email)
                
                # 1. Generate the secure reset token and User ID
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                
                # 2. Build the reset link (Fallback to local IP if reverse fails)
                try:
                    reset_url = request.build_absolute_uri(reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token}))
                except:
                    reset_url = f"http://127.0.0.1:8000/reset/{uid}/{token}/"
                
                # 3. MOCK EMAIL: Print to terminal so you can test it instantly!
                print("\n" + "="*30)
                print(f"📧 MOCK EMAIL TO: {email}")
                print(f"🔗 CLICK THIS LINK TO RESET: {reset_url}")
                print("="*30 + "\n")

                # 4. Try sending the real email via Gmail
                try:
                    send_mail(
                        'Fixora - Password Reset',
                        f'Hello {user.first_name},\n\nClick here to reset your password:\n{reset_url}\n\nIf you did not request this, please ignore this email.',
                        'hnikumbh17@gmail.com', # Your sending email
                        [user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"⚠️ Real Email Failed. Error: {e}")
                
                messages.success(request, 'Password reset link sent! Please check your email inbox.')
                return redirect('login') 
                
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email address.')

    return render(request, 'file/forgot_password.html')


def verify_otp(request):
    # If they try to visit this page without entering a phone number first, kick them back
    if 'reset_phone' not in request.session:
        return redirect('forgot_password')
        
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Retrieve the generated OTP and Phone from the session
        saved_otp = request.session.get('reset_otp')
        phone = request.session.get('reset_phone')
        
        if entered_otp == saved_otp:
            if new_password == confirm_password:
                # Find the user and save the new password
                user = User.objects.get(phone=phone)
                user.set_password(new_password) # This safely encrypts the new password!
                user.save()
                
                # Delete the temporary session data so it can't be used again
                del request.session['reset_phone']
                del request.session['reset_otp']
                
                messages.success(request, 'Password reset successfully! You can now log in.')
                return redirect('login') # Assuming your login url is named 'login'
            else:
                messages.error(request, 'Passwords do not match. Try again.')
        else:
            messages.error(request, 'Invalid OTP. Please check your text messages.')
            
    return render(request, 'file/verify_otp.html')