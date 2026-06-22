from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
class Society(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class User(AbstractUser):

    ROLE_CHOICES = (
        ('superadmin', 'System Super Admin'),
        ('admin', 'Admin'),
        ('resident', 'Resident'),
        ('worker', 'Worker'),
    )

    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='resident')
    phone = models.CharField(max_length=15, blank=True, null=True)

    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users'
    )

    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True
    )

    otp = models.CharField(max_length=6, blank=True, null=True)

    otp_created_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    


class Complaint(models.Model):
    CATEGORY_CHOICES = (
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('cleaning', 'Cleaning'),
        ('tiles', 'Tiles'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )

    # Added Priority Choices
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )

    resident = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='low') # New Field
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True) # New Field
    image = models.ImageField(upload_to='complaints/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')

    def __str__(self):
        return f"{self.title} - {self.status}"
    
class ServiceBooking(models.Model):

    CATEGORY_CHOICES = (
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('cleaning', 'Cleaning'),
        ('glass', 'Glass'),
        ('tiles', 'Tiles'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('assigned', 'Worker Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    resident = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_bookings'
    )

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='plumbing'
    )

    preferred_date = models.DateField(
        blank=True,
        null=True
    )

    preferred_time_slot = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    location = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    additional_notes = models.TextField(
        blank=True,
        null=True
    )

    image = models.ImageField(
        upload_to='services/',
        blank=True,
        null=True
    )

    worker_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    worker_phone = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    estimated_arrival = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    assigned_worker = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='worker_complaints'
    )

    worker_notes = models.TextField(
        blank=True,
        null=True
    )

    completion_image = models.ImageField(
        upload_to='completed_works/',
        blank=True,
        null=True
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.resident.username} - {self.category} ({self.status})"

class Alert(models.Model):

    ALERT_TYPES = (
        ('complaint', 'Complaint'),
        ('service', 'Service'),
        ('general', 'General'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='alerts'
    )

    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        related_name='alerts',
        null=True,
        blank=True
    )

    title = models.CharField(max_length=255)

    message = models.TextField()

    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_TYPES,
        default='general'
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

