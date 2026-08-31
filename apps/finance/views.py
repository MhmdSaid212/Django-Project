"""HTML views. Keep these thin — call services, do not query MongoDB here."""
from core.constants import UserRole
from core.permissions import login_required, role_required
from core.wireframes import wireframe


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def customer_balances(request):
    return wireframe(request, "finance/customer_balances.html", "Customer balances", heading="Customer balances")


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def supplier_balances(request):
    return wireframe(request, "finance/supplier_balances.html", "Supplier balances", heading="Supplier balances")


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def receivables(request):
    return wireframe(request, "finance/receivables.html", "Accounts receivable", heading="Accounts receivable")


@login_required
@role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def payables(request):
    return wireframe(request, "finance/payables.html", "Accounts payable", heading="Accounts payable")
