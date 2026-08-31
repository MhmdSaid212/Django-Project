"""HTML views. Keep these thin — call services, do not query MongoDB here."""
from core.constants import UserRole
from core.permissions import login_required, role_required
from core.wireframes import record, wireframe


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def invoice_list(request):
    return wireframe(request, "invoices/list.html", "Invoices", heading="Invoices")


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def invoice_detail(request, id):
    row = record("invoice", id)
    return wireframe(
        request,
        "invoices/detail.html",
        row["number"],
        heading=row["number"],
        crumbs=[{"label": "Invoices", "url": "/invoices/"}, {"label": row["number"], "url": ""}],
        record=row,
    )


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def invoice_print(request, id):
    row = record("invoice", id)
    return wireframe(request, "invoices/print.html", "Print " + row["number"], heading=row["number"], record=row)
