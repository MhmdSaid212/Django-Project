from django.urls import path

from core.access import FINANCE_ROLES, OPERATIONS_ROLES, OWNER_ROLES
from core.http import unimplemented

app_name = "dashboard_api"

urlpatterns = [
    path(
        "agent/",
        unimplemented(
            "GET",
            message="GET /api/dashboard/agent/ is not implemented yet. Owner: Dev 1.",
            roles=OPERATIONS_ROLES,
        ),
        name="agent",
    ),
    path(
        "accountant/",
        unimplemented(
            "GET",
            message="GET /api/dashboard/accountant/ is not implemented yet. Owner: Dev 4.",
            roles=FINANCE_ROLES,
        ),
        name="accountant",
    ),
    path(
        "owner/",
        unimplemented(
            "GET",
            message="GET /api/dashboard/owner/ is not implemented yet. Owner: Dev 4.",
            roles=OWNER_ROLES,
        ),
        name="owner",
    ),
]
