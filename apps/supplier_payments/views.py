from core.constants import UserRole
from core.permissions import login_required, role_required
from core.wireframes import record, wireframe


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def supplier_payment_list(request):
    return wireframe(request, "supplier_payments/list.html", "Supplier payments", heading="Supplier payments")


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def supplier_payment_detail(request, id):
    row = record("sp", id)
    return wireframe(
        request,
        "supplier_payments/detail.html",
        row["number"],
        heading=row["number"],
        crumbs=[{"label": "Supplier payments", "url": "/supplier-payments/"}, {"label": row["number"], "url": ""}],
        record=row,
    )
