"""HTML views. Keep these thin — call services, do not query MongoDB here."""
from core.constants import UserRole
from core.permissions import login_required, role_required
from core.wireframes import wireframe


@login_required
@role_required(UserRole.OWNER_ADMIN)
def audit_list(request):
    return wireframe(request, "audit/list.html", "Audit logs", heading="Activity timeline")
