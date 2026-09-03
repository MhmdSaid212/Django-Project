from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.customers.forms import CustomerForm
from apps.customers.services import CustomerService
from core.access import OPERATIONS_ROLES
from core.exceptions import DatabaseUnavailableError, TourOpsError
from core.permissions import get_session_user, login_required, role_required


def _unavailable(request):
    messages.error(request, "Cannot reach MongoDB. Check MONGODB_URI and that MongoDB is running.")
    return redirect("customers:list")


@login_required
@role_required(*OPERATIONS_ROLES)
def customer_list(request):
    try:
        customers = CustomerService().list_presented()
    except DatabaseUnavailableError:
        messages.error(request, "Cannot reach MongoDB. Customers are unavailable.")
        customers = []
    return render(
        request,
        "customers/list.html",
        {"page_title": "Customers", "page_heading": "Customers", "customers": customers},
    )


@login_required
@role_required(*OPERATIONS_ROLES)
@require_http_methods(["GET", "POST"])
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            customer = CustomerService().create(actor_id=get_session_user(request)["id"], **form.cleaned_data)
        except DatabaseUnavailableError:
            return _unavailable(request)
        except TourOpsError as extra:
            messages.error(request, extra.message)
        else:
            messages.success(request, f"Created {customer['customer_number']}.")
            return redirect("customers:detail", id=str(customer["_id"]))
    return render(
        request,
        "customers/form.html",
        {"form": form, "page_title": "New customer", "page_heading": "New customer", "submit_label": "Save customer"},
    )


@login_required
@role_required(*OPERATIONS_ROLES)
def customer_detail(request, id):
    try:
        record = CustomerService().get_presented(id)
    except DatabaseUnavailableError:
        return _unavailable(request)
    except TourOpsError:
        messages.error(request, "Customer not found.")
        return redirect("customers:list")
    return render(
        request,
        "customers/detail.html",
        {
            "page_title": record["name"],
            "page_heading": record["name"],
            "crumbs": [{"label": "Customers", "url": reverse("customers:list")}, {"label": record["number"], "url": ""}],
            "record": record,
            "tab": request.GET.get("tab") or "overview",
        },
    )


@login_required
@role_required(*OPERATIONS_ROLES)
@require_http_methods(["GET", "POST"])
def customer_edit(request, id):
    messages.info(request, "Customer editing will follow in a later slice. Create a new record if needed.")
    return redirect("customers:detail", id=id)
