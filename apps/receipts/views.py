"""HTML views. Keep these thin — call services, do not query MongoDB here."""
from core.constants import UserRole
from core.permissions import login_required, role_required
from core.wireframes import record, wireframe


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def receipt_list(request):
    return wireframe(request, "receipts/list.html", "Receipts", heading="Receipts")


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def receipt_detail(request, id):
    row = record("receipt", id)
    return wireframe(
        request,
        "receipts/detail.html",
        row["number"],
        heading=row["number"],
        crumbs=[{"label": "Receipts", "url": "/receipts/"}, {"label": row["number"], "url": ""}],
        record=row,
    )
