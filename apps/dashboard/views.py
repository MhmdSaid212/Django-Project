from django.shortcuts import redirect
from django.urls import reverse

from apps.accounts.views import dashboard_for_role
from core.constants import UserRole
from core.permissions import get_session_user, login_required, role_required
from core.wireframes import wireframe


@login_required
def home(request):
    user = get_session_user(request)
    return redirect(reverse(dashboard_for_role(user["role"])))


def _dashboard(request, title: str):
    return wireframe(
        request,
        "dashboard/command.html",
        title,
        heading="Operations command center",
        lead="Here’s what needs attention across bookings, finance, and upcoming tours.",
    )


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def agent(request):
    return _dashboard(request, "Agent dashboard")


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def accountant(request):
    return _dashboard(request, "Accountant dashboard")


@login_required
@role_required(UserRole.OWNER_ADMIN)
def owner(request):
    return _dashboard(request, "Owner dashboard")
