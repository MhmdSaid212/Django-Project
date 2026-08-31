"""HTML views. Keep these thin — call services, do not query MongoDB here."""
from core.constants import UserRole
from core.permissions import login_required, role_required
from core.wireframes import record, wireframe


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def booking_list(request):
    return wireframe(request, "bookings/list.html", "Bookings", heading="Bookings")


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def booking_create(request):
    return wireframe(request, "bookings/create.html", "Create booking", heading="New booking")


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def booking_detail(request, id):
    row = record("booking", id)
    return wireframe(
        request,
        "bookings/detail.html",
        row["number"],
        heading=row["number"],
        crumbs=[{"label": "Bookings", "url": "/bookings/"}, {"label": row["number"], "url": ""}],
        record=row,
    )
