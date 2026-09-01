from core.constants import UserRole
from core.permissions import login_required, role_required
from core.wireframes import record, wireframe


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def expense_list(request):
    return wireframe(request, "expenses/list.html", "Expenses", heading="Expenses")


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def expense_create(request):
    return wireframe(request, "expenses/form.html", "Create expense", heading="New expense")


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def expense_detail(request, id):
    row = record("expense", id)
    return wireframe(
        request,
        "expenses/detail.html",
        row["number"],
        heading=row["number"],
        crumbs=[{"label": "Expenses", "url": "/expenses/"}, {"label": row["number"], "url": ""}],
        record=row,
    )
