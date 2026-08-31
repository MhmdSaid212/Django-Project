"""
Authentication and role helpers.

TourOps users live in MongoDB (users collection), not Django's auth.User.
We store a small, non-secret snapshot in the signed-cookie session:

    user_id, email, first_name, last_name, role

Do not put password_hash in the session.
"""
from __future__ import annotations

from functools import wraps
from typing import Callable

from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse

from core.constants import UserRole
from core.responses import error_response

SESSION_USER_KEY = "tourops_user"


def get_session_user(request: HttpRequest) -> dict | None:
    return request.session.get(SESSION_USER_KEY)


def set_session_user(request: HttpRequest, user: dict) -> None:
    request.session[SESSION_USER_KEY] = {
        "id": str(user["_id"]),
        "email": user.get("email"),
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "role": user.get("role"),
    }
    request.session.cycle_key()


def clear_session_user(request: HttpRequest) -> None:
    request.session.flush()


def is_authenticated(request: HttpRequest) -> bool:
    return get_session_user(request) is not None


def _wants_json(request: HttpRequest) -> bool:
    return request.path.startswith("/api/") or "application/json" in request.headers.get(
        "Accept", ""
    )


def login_required(view: Callable) -> Callable:
    """Require a logged-in TourOps user (MongoDB session)."""

    @wraps(view)
    def wrapper(request: HttpRequest, *args, **kwargs):
        if not is_authenticated(request):
            if _wants_json(request):
                return error_response("UNAUTHENTICATED", "Login required.", status=401)
            login_url = reverse("accounts:login")
            return redirect(f"{login_url}?next={request.path}")
        return view(request, *args, **kwargs)

    return wrapper


def role_required(*roles: str) -> Callable:
    """
    Require one of the given roles.

    Usage:
        @role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
        def invoice_list(request):
            ...
    """
    allowed = {getattr(role, "value", role) for role in roles}

    def decorator(view: Callable) -> Callable:
        @wraps(view)
        @login_required
        def wrapper(request: HttpRequest, *args, **kwargs):
            user = get_session_user(request) or {}
            if user.get("role") not in allowed:
                if _wants_json(request):
                    return error_response(
                        "PERMISSION_DENIED",
                        "You do not have permission to access this resource.",
                        status=403,
                    )
                return render(request, "errors/403.html", status=403)
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


def owner_required(view: Callable) -> Callable:
    return role_required(UserRole.OWNER_ADMIN)(view)


def staff_required(view: Callable) -> Callable:
    """Any authenticated role (agent, accountant, or owner)."""
    return role_required(
        UserRole.TRAVEL_AGENT,
        UserRole.ACCOUNTANT,
        UserRole.OWNER_ADMIN,
    )(view)
