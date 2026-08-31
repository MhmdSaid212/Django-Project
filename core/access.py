"""
Permission helpers that views can call besides the decorators.

Keep role checks in one place so the four developers do not invent
incompatible rules.
"""
from core.constants import UserRole
from core.permissions import get_session_user

# Who may see operations screens (customers, tours, bookings, packages).
OPERATIONS_ROLES = {UserRole.TRAVEL_AGENT.value, UserRole.OWNER_ADMIN.value}

# Who may see finance transaction screens.
FINANCE_ROLES = {UserRole.ACCOUNTANT.value, UserRole.OWNER_ADMIN.value}

# Who may see reports.
REPORT_ROLES = {UserRole.ACCOUNTANT.value, UserRole.OWNER_ADMIN.value}

# Owner-only screens.
OWNER_ROLES = {UserRole.OWNER_ADMIN.value}

# All authenticated staff.
ALL_ROLES = {
    UserRole.TRAVEL_AGENT.value,
    UserRole.ACCOUNTANT.value,
    UserRole.OWNER_ADMIN.value,
}


def user_role(request) -> str | None:
    user = get_session_user(request)
    return user.get("role") if user else None


def has_role(request, *roles: str) -> bool:
    role = user_role(request)
    return role in {getattr(r, "value", r) for r in roles}


def can_access_operations(request) -> bool:
    return has_role(request, *OPERATIONS_ROLES)


def can_access_finance(request) -> bool:
    return has_role(request, *FINANCE_ROLES)
