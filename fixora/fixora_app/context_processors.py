from .models import Alert

def unread_alerts(request):
    if request.user.is_authenticated:
        # Count only unread alerts belonging to the logged-in user
        count = Alert.objects.filter(user=request.user, is_read=False).count()
        return {'unread_alerts_count': count}
    return {'unread_alerts_count': 0}