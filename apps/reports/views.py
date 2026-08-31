from core.constants import UserRole
from core.permissions import login_required, role_required
from core.wireframes import record, wireframe


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def report_list(request):
    return wireframe(request, "reports/list.html", "Reports", heading="Financial reports")


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def report_revenue(request):
    return wireframe(request, "reports/revenue.html", "Revenue vs cost", heading="Revenue vs cost")


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def report_expenses(request):
    return wireframe(request, "reports/expenses.html", "Expense breakdown", heading="Expense breakdown")


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def report_profit_loss(request):
    return wireframe(request, "reports/profit_loss.html", "Cash flow", heading="Cash flow")


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def tour_profitability(request):
    ident = request.GET.get("tour")
    selected = record("tour", ident) if ident else None
    return wireframe(
        request,
        "reports/profitability.html",
        "Tour profitability",
        heading="Tour profitability",
        selected=selected,
    )
