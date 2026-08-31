from django.urls import path

from core.http import unimplemented

app_name = "dashboard_api"

urlpatterns = [
    path(
        "agent/",
        unimplemented("GET", message="GET /api/dashboard/agent/ is not implemented yet. Owner: Dev 1."),
        name="agent",
    ),
    path(
        "accountant/",
        unimplemented("GET", message="GET /api/dashboard/accountant/ is not implemented yet. Owner: Dev 4."),
        name="accountant",
    ),
    path(
        "owner/",
        unimplemented("GET", message="GET /api/dashboard/owner/ is not implemented yet. Owner: Dev 4."),
        name="owner",
    ),
]
