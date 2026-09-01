from core.constants import UserRole
from core.permissions import login_required, role_required
from core.wireframes import record, wireframe


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def refund_list(request):
    return wireframe(request, "refunds/list.html", "Refunds", heading="Refunds")


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def refund_detail(request, id):
    row = record("refund", id)
    return wireframe(
        request,
        "refunds/detail.html",
        row["number"],
        heading=row["number"],
        crumbs=[{"label": "Refunds", "url": "/refunds/"}, {"label": row["number"], "url": ""}],
        record=row,
    )
