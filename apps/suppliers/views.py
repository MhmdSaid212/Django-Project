from core.constants import UserRole
from core.permissions import login_required, role_required
from core.wireframes import record, wireframe


def _directory(request, title, heading, type_filter=None):
    return wireframe(
        request,
        "suppliers/list.html",
        title,
        heading=heading,
        type_filter=type_filter,
    )


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def supplier_list(request):
    return _directory(request, "Suppliers", "Supplier directory")


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def supplier_create(request):
    return wireframe(request, "suppliers/form.html", "Create supplier", heading="New supplier")


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def hotels(request):
    return _directory(request, "Hotels", "Hotels", "HOTEL")


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def transportation(request):
    return _directory(request, "Transportation", "Transportation", "TRANSPORTATION")


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def tour_guides(request):
    return _directory(request, "Tour guides", "Tour guides", "TOUR_GUIDE")


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def other_suppliers(request):
    return _directory(request, "Other suppliers", "Other suppliers", "OTHER")


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def supplier_detail(request, id):
    row = record("supplier", id)
    return wireframe(
        request,
        "suppliers/detail.html",
        row["name"],
        heading=row["name"],
        crumbs=[{"label": "Suppliers", "url": "/suppliers/"}, {"label": row["number"], "url": ""}],
        record=row,
        tab=request.GET.get("tab", "overview"),
    )


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def supplier_edit(request, id):
    row = record("supplier", id)
    return wireframe(request, "suppliers/form.html", "Edit supplier", heading="Edit " + row["name"], record=row)
