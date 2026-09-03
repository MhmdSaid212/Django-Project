from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.supplier_payments.services import SupplierPaymentService
from apps.supplier_reservations.services import SupplierReservationService
from apps.suppliers.forms import SupplierForm, initial_from_record
from apps.suppliers.services import SupplierService
from core.access import ALL_ROLES
from core.constants import RecordStatus, SupplierType
from core.exceptions import DatabaseUnavailableError, TourOpsError
from core.permissions import get_session_user, login_required, role_required


_INFO_KEYS = (
    "star_rating",
    "room_count",
    "board_basis",
    "check_in_time",
    "check_out_time",
    "room_types",
    "amenities",
    "vehicle_type",
    "fleet_size",
    "seats_per_vehicle",
    "license_number",
    "coverage_areas",
    "languages",
    "years_experience",
    "specialties",
    "iata_code",
    "alliance",
    "activity_kinds",
    "typical_duration_hours",
    "location",
    "cuisine",
    "seating_capacity",
    "meal_types",
    "policy_types",
    "coverage_notes",
    "details",
)


def _unavailable(request, next_name="suppliers:list"):
    messages.error(request, "Cannot reach MongoDB. Check MONGODB_URI and that MongoDB is running.")
    return redirect(next_name)


def _form_payload(form: SupplierForm) -> dict:
    data = form.cleaned_data
    payload = {
        "name": data["name"],
        "supplier_type": data["supplier_type"],
        "contact_person": data.get("contact_person"),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "country": data.get("country"),
        "city": data.get("city"),
        "street": data.get("street"),
        "tax_number": data.get("tax_number"),
        "payment_terms": data.get("payment_terms"),
        "bank_name": data.get("bank_name"),
        "account_name": data.get("account_name"),
        "iban": data.get("iban"),
        "notes": data.get("notes"),
    }
    for key in _INFO_KEYS:
        if key in data:
            payload[key] = data[key]
    if data.get("supplier_type") == SupplierType.TOUR_GUIDE.value:
        payload["license_number"] = data.get("guide_license_number")
    if "status" in data and data.get("status"):
        payload["status"] = data["status"]
    return payload


def _directory(request, title, heading, *, supplier_type=None, group=None, type_filter=None):
    service = SupplierService()
    query = (request.GET.get("q") or "").strip().lower()
    status = (request.GET.get("status") or "").strip().upper()
    type_query = (request.GET.get("type") or "").strip().upper() or None
    chip_type = type_query or type_filter or supplier_type
    effective_type = supplier_type or (None if group else (type_query or type_filter))
    try:
        suppliers = service.list_presented(
            supplier_type=effective_type,
            group=group,
            status=status or None,
        )
        reservations = SupplierReservationService().list_presented()
    except DatabaseUnavailableError:
        messages.error(request, "Cannot reach MongoDB. Suppliers are unavailable.")
        suppliers, reservations = [], []
    except TourOpsError as extra:
        messages.error(request, extra.message)
        suppliers, reservations = [], []
    open_by_supplier = {}
    tours_by_supplier = {}
    for row in reservations:
        if row.get("is_cancelled"):
            continue
        key = row.get("supplier_id")
        open_by_supplier[key] = open_by_supplier.get(key, 0) + 1
        tours_by_supplier.setdefault(key, set()).add(row.get("tour_id"))
    if query:
        suppliers = [
            row
            for row in suppliers
            if query in (row.get("name") or "").lower()
            or query in (row.get("number") or "").lower()
            or query in (row.get("email") or "").lower()
        ]
    for row in suppliers:
        row["open_reservations"] = open_by_supplier.get(row["id"], 0)
        row["tour_count"] = len(tours_by_supplier.get(row["id"], set())) or len(row.get("tours") or [])
    all_for_stats = suppliers if (effective_type or group or query or status) else None
    try:
        universe = service.list_presented() if all_for_stats is not None else suppliers
    except (DatabaseUnavailableError, TourOpsError):
        universe = suppliers
    stats = {
        "total": len(universe),
        "active": sum(1 for row in universe if row.get("status") == RecordStatus.ACTIVE.value),
        "hotels": sum(1 for row in universe if row.get("type") == SupplierType.HOTEL.value),
        "transport": sum(1 for row in universe if row.get("type") == SupplierType.TRANSPORTATION.value),
        "guides": sum(1 for row in universe if row.get("type") == SupplierType.TOUR_GUIDE.value),
        "owed": sum((row.get("owed") or 0) for row in universe),
    }
    return render(
        request,
        "suppliers/list.html",
        {
            "page_title": title,
            "page_heading": heading,
            "suppliers": suppliers,
            "type_filter": chip_type,
            "q": request.GET.get("q") or "",
            "status_filter": status,
            "stats": stats,
        },
    )


@login_required
@role_required(*ALL_ROLES)
def supplier_list(request):
    type_filter = (request.GET.get("type") or "").strip().upper() or None
    return _directory(request, "Suppliers", "Suppliers", supplier_type=type_filter, type_filter=type_filter)


@login_required
@role_required(*ALL_ROLES)
@require_http_methods(["GET", "POST"])
def supplier_create(request):
    form = SupplierForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            supplier = SupplierService().create(actor_id=get_session_user(request)["id"], **_form_payload(form))
        except DatabaseUnavailableError:
            return _unavailable(request)
        except TourOpsError as extra:
            messages.error(request, extra.message)
        else:
            messages.success(request, f"Created {supplier['supplier_number']}.")
            return redirect("suppliers:detail", id=str(supplier["_id"]))
    return render(
        request,
        "suppliers/form.html",
        {
            "form": form,
            "page_title": "New supplier",
            "page_heading": "New supplier",
            "submit_label": "Save supplier",
        },
    )


@login_required
@role_required(*ALL_ROLES)
def hotels(request):
    return _directory(request, "Hotels", "Hotels", supplier_type="HOTEL", type_filter="HOTEL")


@login_required
@role_required(*ALL_ROLES)
def transportation(request):
    return _directory(request, "Transportation", "Transportation", supplier_type="TRANSPORTATION", type_filter="TRANSPORTATION")


@login_required
@role_required(*ALL_ROLES)
def tour_guides(request):
    return _directory(request, "Tour guides", "Tour guides", supplier_type="TOUR_GUIDE", type_filter="TOUR_GUIDE")


@login_required
@role_required(*ALL_ROLES)
def other_suppliers(request):
    return _directory(request, "Other suppliers", "Other suppliers", group="OTHER", type_filter="OTHER")


@login_required
@role_required(*ALL_ROLES)
def supplier_detail(request, id):
    tab = (request.GET.get("tab") or "overview").strip().lower()
    if tab not in {"overview", "tours", "reservations", "expenses", "payments", "activity"}:
        tab = "overview"
    try:
        record = SupplierService().get_presented(id)
        reservations = SupplierReservationService().list_presented(supplier_id=id)
        payments = []
        activity = []
        try:
            from apps.audit.services import AuditService

            activity = AuditService().for_entity("suppliers", id, limit=20)
        except Exception:
            activity = []
        try:
            payments = SupplierPaymentService().list_for_supplier(id)
        except Exception:
            payments = []
        record["reservations"] = reservations
        record["payments"] = payments
        record["activity"] = activity
        record["open_reservation_count"] = sum(1 for row in reservations if not row.get("is_cancelled"))
        record["upcoming_reservations"] = [row for row in reservations if row.get("is_upcoming")]
        record["confirmed_reservations"] = [row for row in reservations if row.get("is_confirmed")]
        record["open_bill_count"] = len(record.get("open_expenses") or [])
    except DatabaseUnavailableError:
        return _unavailable(request)
    except TourOpsError:
        messages.error(request, "Supplier not found.")
        return redirect("suppliers:list")
    return render(
        request,
        "suppliers/detail.html",
        {
            "page_title": record["name"],
            "page_heading": record["name"],
            "crumbs": [
                {"label": "Suppliers", "url": reverse("suppliers:list")},
                {"label": record["number"], "url": ""},
            ],
            "record": record,
            "tab": tab,
        },
    )


@login_required
@role_required(*ALL_ROLES)
@require_http_methods(["GET", "POST"])
def supplier_edit(request, id):
    service = SupplierService()
    try:
        record = service.get_presented(id, include_extras=False)
    except DatabaseUnavailableError:
        return _unavailable(request)
    except TourOpsError:
        messages.error(request, "Supplier not found.")
        return redirect("suppliers:list")

    form = SupplierForm(request.POST or None, initial=initial_from_record(record), include_status=True)
    if request.method == "POST" and form.is_valid():
        try:
            service.update(id, actor_id=get_session_user(request)["id"], **_form_payload(form))
        except DatabaseUnavailableError:
            return _unavailable(request)
        except TourOpsError as extra:
            messages.error(request, extra.message)
        else:
            messages.success(request, f"Updated {record['number']}.")
            return redirect("suppliers:detail", id=id)
    return render(
        request,
        "suppliers/form.html",
        {
            "form": form,
            "page_title": f"Edit {record['name']}",
            "page_heading": f"Edit {record['name']}",
            "submit_label": "Save changes",
            "record": record,
        },
    )


@login_required
@role_required(*ALL_ROLES)
@require_POST
def supplier_delete(request, id):
    try:
        SupplierService().soft_delete(id, actor_id=get_session_user(request)["id"])
    except DatabaseUnavailableError:
        return _unavailable(request)
    except TourOpsError as extra:
        messages.error(request, extra.message)
        return redirect("suppliers:detail", id=id)
    messages.success(request, "Supplier deleted.")
    return redirect("suppliers:list")
