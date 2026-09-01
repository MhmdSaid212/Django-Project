from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts.forms import (
    ChangePasswordForm,
    ChangeRoleForm,
    LoginForm,
    PasswordResetRequestForm,
    ResetPasswordForm,
    StaffUserForm,
)
from apps.accounts.services import AuthService, UserService, present_user
from core.access import dashboard_for_role
from core.constants import UserRole, UserStatus
from core.exceptions import DatabaseUnavailableError, TourOpsError
from core.permissions import (
    clear_session_user,
    get_session_user,
    login_required,
    role_required,
    safe_next_url,
    set_session_user,
)
from core.wireframes import wireframe


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
            next_url = safe_next_url(request, request.POST.get("next") or request.GET.get("next"))
            return redirect(next_url or reverse(dashboard_for_role(user["role"])))

    return render(
        request,
        "accounts/login.html",
        {"form": form, "page_title": "Sign in", "next": request.GET.get("next") or request.POST.get("next") or ""},
    )


@require_http_methods(["GET", "POST"])
def logout_view(request):
    if request.method == "GET":
        if not get_session_user(request):
            return redirect("accounts:login")
        return render(request, "accounts/logout.html", {"page_title": "Sign out"})
    clear_session_user(request)
    messages.success(request, "You have been signed out.")
    return redirect("accounts:login")


@require_http_methods(["GET", "POST"])
def password_reset_view(request):
    if get_session_user(request):
        return redirect("accounts:password")

    form = PasswordResetRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            AuthService().reset_password_by_email(
                form.cleaned_data["email"],
                form.cleaned_data["new_password"],
            )
        except DatabaseUnavailableError:
            messages.error(request, "Cannot reach MongoDB. Check MONGODB_URI and that MongoDB is running.")
        except TourOpsError as exc:
            messages.error(request, exc.message)
        else:
            messages.success(request, "Password updated. You can sign in with your new password.")
            return redirect("accounts:login")

    return render(
        request,
        "accounts/password_reset.html",
        {"form": form, "page_title": "Reset password"},
    )


@login_required
@require_http_methods(["GET", "POST"])
def change_password(request):
    form = ChangePasswordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            AuthService().change_password(
                get_session_user(request)["id"],
                form.cleaned_data["current_password"],
                form.cleaned_data["new_password"],
            )
        except TourOpsError as exc:
            messages.error(request, exc.message)
        else:
            messages.success(request, "Your password has been updated.")
            return redirect("accounts:password")
    return render(
        request,
        "accounts/password.html",
        {"form": form, "page_title": "Change password", "page_heading": "Change password"},
    )


@login_required
@role_required(UserRole.OWNER_ADMIN)
def users_list(request):
    try:
        users = UserService().list_users()
    except DatabaseUnavailableError:
        messages.error(request, "Cannot reach MongoDB. Staff directory is unavailable.")
        users = []
    return render(
        request,
        "accounts/users.html",
        {"page_title": "Users", "page_heading": "Staff directory", "users": users},
    )


@login_required
@role_required(UserRole.OWNER_ADMIN)
@require_http_methods(["GET", "POST"])
def user_create(request):
    form = StaffUserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            user = UserService().create_user(
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                role=form.cleaned_data["role"],
                phone=form.cleaned_data["phone"],
            )
        except TourOpsError as exc:
            messages.error(request, exc.message)
        else:
            messages.success(request, f"Created {present_user(user)['name']}.")
            return redirect("accounts:user_detail", id=str(user["_id"]))
    return render(
        request,
        "accounts/user_form.html",
        {"form": form, "page_title": "New user", "page_heading": "Invite staff"},
    )


@login_required
@role_required(UserRole.OWNER_ADMIN)
@require_http_methods(["GET", "POST"])
def user_detail(request, id):
    service = UserService()
    try:
        record = service.get_presented(id)
    except DatabaseUnavailableError:
        messages.error(request, "Cannot reach MongoDB.")
        return redirect("accounts:users")
    except TourOpsError:
        messages.error(request, "User not found.")
        return redirect("accounts:users")

    role_form = ChangeRoleForm(initial={"role": record["role"]})
    password_form = ResetPasswordForm()
    current_id = get_session_user(request)["id"]
    is_self = record["id"] == current_id

    return render(
        request,
        "accounts/user_detail.html",
        {
            "page_title": record["name"],
            "page_heading": record["name"],
            "crumbs": [{"label": "Users", "url": reverse("accounts:users")}, {"label": record["name"], "url": ""}],
            "record": record,
            "role_form": role_form,
            "password_form": password_form,
            "is_self": is_self,
        },
    )


@login_required
@role_required(UserRole.OWNER_ADMIN)
@require_POST
def user_set_status(request, id):
    next_status = request.POST.get("status")
    try:
        UserService().set_status(id, next_status, actor_id=get_session_user(request)["id"])
    except TourOpsError as exc:
        messages.error(request, exc.message)
    else:
        label = "activated" if next_status == UserStatus.ACTIVE.value else "deactivated"
        messages.success(request, f"User {label}.")
    return redirect("accounts:user_detail", id=id)


@login_required
@role_required(UserRole.OWNER_ADMIN)
@require_POST
def user_change_role(request, id):
    form = ChangeRoleForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Choose a valid role.")
        return redirect("accounts:user_detail", id=id)
    try:
        UserService().change_role(id, form.cleaned_data["role"], actor_id=get_session_user(request)["id"])
    except TourOpsError as exc:
        messages.error(request, exc.message)
    else:
        messages.success(request, "Role updated.")
    return redirect("accounts:user_detail", id=id)


@login_required
@role_required(UserRole.OWNER_ADMIN)
@require_POST
def user_reset_password(request, id):
    form = ResetPasswordForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Passwords must match and be at least 8 characters.")
        return redirect("accounts:user_detail", id=id)
    try:
        UserService().reset_password(
            id,
            form.cleaned_data["new_password"],
            actor_id=get_session_user(request)["id"],
        )
    except TourOpsError as exc:
        messages.error(request, exc.message)
    else:
        messages.success(request, "Password reset.")
    return redirect("accounts:user_detail", id=id)


@login_required
@role_required(UserRole.OWNER_ADMIN)
def settings_page(request):
    return wireframe(request, "accounts/settings.html", "Settings", heading="System settings")
