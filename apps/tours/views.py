"""HTML views. Keep these thin — call services, do not query MongoDB here."""
from core.constants import UserRole
from core.permissions import login_required, role_required
from core.wireframes import record, wireframe


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def tour_list(request):
    return wireframe(request, "tours/list.html", "Tours", heading="Departures")


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def tour_create(request):
    return wireframe(request, "tours/form.html", "Create tour", heading="New departure")


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def tour_detail(request, id):
    row = record("tour", id)
    return wireframe(
        request,
        "tours/detail.html",
        row["name"],
        heading=row["name"],
        crumbs=[{"label": "Tours", "url": "/tours/"}, {"label": row["code"], "url": ""}],
        record=row,
        tab=request.GET.get("tab", "overview"),
    )


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def tour_edit(request, id):
    row = record("tour", id)
    return wireframe(request, "tours/form.html", "Edit tour", heading="Edit " + row["name"], record=row)


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def availability(request):
    return wireframe(request, "tours/availability.html", "Availability", heading="Seat availability")
