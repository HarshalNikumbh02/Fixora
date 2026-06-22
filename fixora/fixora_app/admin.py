from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    User,
    Society,
    Complaint,
    ServiceBooking,
    Alert
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        (
            'Extra Information',
            {
                'fields': (
                    'role',
                    'phone',
                    'society',
                    'profile_image',
                )
            },
        ),
    )

    list_display = (
        'username',
        'email',
        'role',
        'society',
        'is_staff',
    )


admin.site.register(Society)
admin.site.register(Complaint)
admin.site.register(ServiceBooking)
admin.site.register(Alert)