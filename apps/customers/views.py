from core.constants import UserRole
from core.permissions import login_required, role_required
from core.wireframes import record, wireframe


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def customer_list(request):
    return wireframe(request, "customers/list.html", "Customers", heading="Customers")


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def customer_create(request):
    return wireframe(request, "customers/form.html", "Create customer", heading="New customer")


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def customer_detail(request, id):
    row = record("customer", id)
    return wireframe(
        request,
        "customers/detail.html",
        row["name"],
        heading=row["name"],
        crumbs=[{"label": "Customers", "url": "/customers/"}, {"label": row["number"], "url": ""}],
        record=row,
        tab=request.GET.get("tab", "overview"),
    )


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def customer_edit(request, id):
    row = record("customer", id)
    return wireframe(request, "customers/form.html", "Edit customer", heading="Edit " + row["name"], record=row)
