from core.permissions import login_required
from core.wireframes import wireframe


@login_required
def notification_list(request):
    return wireframe(request, "notifications/list.html", "Notifications", heading="Notification center")
