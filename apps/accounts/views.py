from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.accounts.forms import LoginForm
from apps.accounts.services import AuthService
from core.constants import UserRole
from core.exceptions import DatabaseUnavailableError, TourOpsError
from core.permissions import (
    clear_session_user,
    get_session_user,
    login_required,
    role_required,
    set_session_user,
)
from core.wireframes import record, wireframe

DASHBOARD_BY_ROLE = {
    UserRole.TRAVEL_AGENT.value: "dashboard:agent",
    UserRole.ACCOUNTANT.value: "dashboard:accountant",
    UserRole.OWNER_ADMIN.value: "dashboard:owner",
}


def dashboard_for_role(role: str) -> str:
    return DASHBOARD_BY_ROLE.get(role, "dashboard:owner")


@require_http_methods(["GET", "POST"])
def login_view(request):
    if get_session_user(request):
        return redirect(dashboard_for_role(get_session_user(request)["role"]))

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            user = AuthService().authenticate(
                form.cleaned_data["email"],
                form.cleaned_data["password"],
            )
        except DatabaseUnavailableError:
            messages.error(request, "Cannot reach MongoDB. Check MONGODB_URI and that MongoDB is running.")
        except TourOpsError as exc:
            messages.error(request, exc.message)
        else:
            set_session_user(request, user)
            messages.success(request, f"Welcome back, {user.get('first_name') or user.get('email')}.")
            next_url = request.GET.get("next")
            return redirect(next_url or reverse(dashboard_for_role(user["role"])))

    return render(request, "accounts/login.html", {"form": form, "page_title": "Sign in"})


def logout_view(request):
    clear_session_user(request)
    messages.success(request, "You have been signed out.")
    return redirect("accounts:login")


@login_required
@role_required(UserRole.OWNER_ADMIN)
def users_list(request):
    return wireframe(request, "accounts/users.html", "Users", heading="Staff directory")


@login_required
@role_required(UserRole.OWNER_ADMIN)
def user_detail(request, id):
    row = record("user", id)
    return wireframe(
        request,
        "accounts/user_detail.html",
        row["name"],
        heading=row["name"],
        crumbs=[{"label": "Users", "url": "/users/"}, {"label": row["name"], "url": ""}],
        record=row,
    )


@login_required
@role_required(UserRole.OWNER_ADMIN)
def settings_page(request):
    return wireframe(request, "accounts/settings.html", "Settings", heading="System settings")
