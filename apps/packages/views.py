from core.constants import UserRole
from core.permissions import login_required, role_required
from core.wireframes import record, wireframe


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def package_list(request):
    return wireframe(request, "packages/list.html", "Packages", heading="Travel packages")


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def package_create(request):
    return wireframe(request, "packages/form.html", "Create package", heading="New package")


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def package_detail(request, id):
    row = record("package", id)
    return wireframe(
        request,
        "packages/detail.html",
        row["name"],
        heading=row["name"],
        crumbs=[{"label": "Packages", "url": "/packages/"}, {"label": row["code"], "url": ""}],
        record=row,
    )


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def package_edit(request, id):
    row = record("package", id)
    return wireframe(request, "packages/form.html", "Edit package", heading="Edit " + row["name"], record=row)
