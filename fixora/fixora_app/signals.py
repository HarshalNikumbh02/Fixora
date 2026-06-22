from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Complaint, ServiceBooking, Alert, User

# -------------------------------------------------------------
# 1. TRACK NEW JOBS (Notifies Workers when a resident posts)
# -------------------------------------------------------------
@receiver(post_save, sender=Complaint)
def complaint_creation_tracker(sender, instance, created, **kwargs):
    if created:
        # Notify all Workers that a new job is available on the board
        workers = User.objects.filter(role='worker', society=instance.resident.society)
        for worker in workers:
            Alert.objects.create(
                user=worker,
                society=instance.resident.society,
                title="New Job Available 🛠️",
                message=f"A new {instance.get_category_display()} issue was reported by {instance.resident.username}.",
                alert_type='complaint'
            )

@receiver(post_save, sender=ServiceBooking)
def service_creation_tracker(sender, instance, created, **kwargs):
    if created:
        # Notify all Workers about new service bookings
        workers = User.objects.filter(role='worker', society=instance.resident.society)
        for worker in workers:
            Alert.objects.create(
                user=worker,
                society=instance.resident.society,
                title="New Service Request 📅",
                message=f"A new {instance.get_category_display()} booking is available.",
                alert_type='service'
            )


# -------------------------------------------------------------
# 2. TRACK STATUS & ASSIGNMENT CHANGES (Notifies Residents & Workers)
# -------------------------------------------------------------
@receiver(pre_save, sender=Complaint)
def complaint_status_tracker(sender, instance, **kwargs):
    if instance.id:
        old_complaint = Complaint.objects.get(id=instance.id)
        
        # A) If an Admin manually assigned this job to a specific worker
        if old_complaint.assigned_worker != instance.assigned_worker and instance.assigned_worker is not None:
            Alert.objects.create(
                user=instance.assigned_worker,
                society=instance.resident.society,
                title="Job Assigned to You 👷",
                message=f"The Admin has assigned you to: {instance.title}.",
                alert_type='complaint'
            )

        # B) If the status progresses (Notify the Resident)
        if old_complaint.status != instance.status:
            if instance.status == 'in_progress':
                Alert.objects.create(
                    user=instance.resident,
                    society=instance.resident.society,
                    title="Worker Assigned 👷‍♂️",
                    message=f"Your complaint '{instance.title}' is now being worked on.",
                    alert_type='complaint'
                )
            elif instance.status == 'completed':
                Alert.objects.create(
                    user=instance.resident,
                    society=instance.resident.society,
                    title="Job Completed ✅",
                    message=f"Your complaint '{instance.title}' has been resolved!",
                    alert_type='complaint'
                )

@receiver(pre_save, sender=ServiceBooking)
def service_status_tracker(sender, instance, **kwargs):
    if instance.id:
        old_service = ServiceBooking.objects.get(id=instance.id)
        
        # A) If an Admin manually assigns a service worker
        if old_service.assigned_worker != instance.assigned_worker and instance.assigned_worker is not None:
            Alert.objects.create(
                user=instance.assigned_worker,
                society=instance.resident.society,
                title="Service Assigned 🔧",
                message=f"You have been assigned to a {instance.get_category_display()} service.",
                alert_type='service'
            )

        # B) If the status progresses (Notify the Resident)
        if old_service.status != instance.status:
            if instance.status == 'assigned':
                Alert.objects.create(
                    user=instance.resident,
                    society=instance.resident.society,
                    title="Service Scheduled 📅",
                    message=f"A worker has been assigned to your {instance.get_category_display()} request.",
                    alert_type='service'
                )
            elif instance.status == 'completed':
                Alert.objects.create(
                    user=instance.resident,
                    society=instance.resident.society,
                    title="Service Completed ✨",
                    message=f"Your {instance.get_category_display()} service has been finished.",
                    alert_type='service'
                )