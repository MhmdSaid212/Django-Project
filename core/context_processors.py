"""Template context available on every page."""
from datetime import datetime

from apps.dashboard.mock_data import MOCK
from core.constants import UserRole
from core.permissions import get_session_user

BRAND = {
    "name": "TourOps",
    "subtitle": "Travel Agency Operations & Finance",
    "tagline": "From Booking to Balance",
}

DASHBOARD_BY_ROLE = {
    UserRole.TRAVEL_AGENT.value: "dashboard:agent",
    UserRole.ACCOUNTANT.value: "dashboard:accountant",
    UserRole.OWNER_ADMIN.value: "dashboard:owner",
}


def branding(request):
    return {"brand": BRAND}


def current_user(request):
    user = get_session_user(request)
    display_name = ""
    initial = "T"
    if user:
        display_name = " ".join(
            part for part in (user.get("first_name"), user.get("last_name")) if part
        ) or user.get("email") or "User"
        initial = (display_name or "U")[0].upper()
    return {
        "current_user": user,
        "current_user_name": display_name,
        "current_user_initial": initial,
        "current_role": user.get("role") if user else None,
        "UserRole": UserRole,
    }


def navigation(request):
    """Role-aware sidebar flags. Templates hide sections the role cannot see."""
    user = get_session_user(request)
    role = user.get("role") if user else None
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    first = (user or {}).get("first_name") or ""
    return {
        "nav": {
            "is_agent": role == UserRole.TRAVEL_AGENT,
            "is_accountant": role == UserRole.ACCOUNTANT,
            "is_owner": role == UserRole.OWNER_ADMIN,
            "ops": role in {UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN},
            "finance": role in {UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN},
            "system": role == UserRole.OWNER_ADMIN,
            "role": role,
            "dashboard": DASHBOARD_BY_ROLE.get(role, "dashboard:home"),
        },
        "greeting": greeting,
        "greeting_name": first or "there",
        "unread_count": MOCK["unread"],
        "today_label": datetime.now().strftime("%A, %d %B %Y"),
    }
