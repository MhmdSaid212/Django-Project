from core.constants import UserRole
from core.permissions import get_session_user

OPERATIONS_ROLES = (UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
FINANCE_ROLES = (UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
REPORT_ROLES = FINANCE_ROLES
OWNER_ROLES = (UserRole.OWNER_ADMIN,)
ALL_ROLES = (UserRole.TRAVEL_AGENT, UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)

DASHBOARD_BY_ROLE = {
    UserRole.TRAVEL_AGENT.value: "dashboard:agent",
    UserRole.ACCOUNTANT.value: "dashboard:accountant",
    UserRole.OWNER_ADMIN.value: "dashboard:owner",
}


def role_values(*roles) -> set[str]:
    return {getattr(role, "value", role) for role in roles}


def user_role(request) -> str | None:
    user = get_session_user(request)
    return user.get("role") if user else None


def has_role(request, *roles) -> bool:
    role = user_role(request)
    return role in role_values(*roles)


def can_access_operations(request) -> bool:
    return has_role(request, *OPERATIONS_ROLES)


def can_access_finance(request) -> bool:
    return has_role(request, *FINANCE_ROLES)


def can_access_reports(request) -> bool:
    return has_role(request, *REPORT_ROLES)


def is_owner(request) -> bool:
    return has_role(request, *OWNER_ROLES)


def dashboard_for_role(role: str) -> str:
    return DASHBOARD_BY_ROLE.get(role, "dashboard:home")
