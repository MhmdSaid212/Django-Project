"""HTML views. Keep these thin — call services, do not query MongoDB here."""
from core.constants import UserRole
from core.permissions import login_required, role_required
from core.wireframes import record, wireframe


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def payment_list(request):
    return wireframe(request, "payments/list.html", "Payments", heading="Payment ledger")


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def payment_detail(request, id):
    row = record("payment", id)
    return wireframe(
        request,
        "payments/detail.html",
        row["number"],
        heading=row["number"],
        crumbs=[{"label": "Payments", "url": "/payments/"}, {"label": row["number"], "url": ""}],
        record=row,
    )
