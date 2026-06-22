from django.core.cache import cache
from django.shortcuts import render

class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only check if maintenance is on AND the user is not a superadmin
        if cache.get('maintenance_mode'):
            # Check if user is authenticated and is NOT a superadmin
            if not (request.user.is_authenticated and getattr(request.user, 'role', None) == 'superadmin'):
                return render(request, 'maintenance.html')
                
        return self.get_response(request)