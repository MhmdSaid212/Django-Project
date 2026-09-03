from collections import OrderedDict

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.packages.services import PackageService
from apps.supplier_reservations.constants import SERVICE_TYPE_LABELS
from apps.supplier_reservations.services import SupplierReservationService
from apps.tours.forms import TourForm, initial_from_package, initial_from_tour
from apps.tours.services import TourService
from core.access import OPERATIONS_ROLES
from core.exceptions import DatabaseUnavailableError, NotFoundError, TourOpsError
from core.permissions import get_session_user, login_required, role_required


def _unavailable(request, next_name="tours:list"):
    messages.error(request, "Cannot reach MongoDB. Check MONGODB_URI and that MongoDB is running.")
    return redirect(next_name)


def _form_payload(form: TourForm) -> dict:
    data = form.cleaned_data
    payload = {
        "name": data.get("name"),
        "package_id": data.get("package_id") or None,
        "city": data.get("city"),
        "country": data.get("country"),
        "start_date": data.get("start_date"),
        "end_date": data.get("end_date"),
        "capacity": data.get("capacity"),
        "selling_price_per_person": data.get("selling_price_per_person"),
        "currency": data.get("currency"),
        "included_services": data.get("included_services"),
        "excluded_services": data.get("excluded_services"),
        "description": data.get("description"),
    }
    if data.get("status"):
        payload["status"] = data["status"]
    return {key: value for key, value in payload.items() if value not in (None, "")}


def _package_choices():
    return PackageService().list_options()


def _reservation_groups(rows):
    buckets = OrderedDict((key, []) for key in SERVICE_TYPE_LABELS)
    extra = []
    for row in rows or []:
        if row.get("is_cancelled"):
            continue
        key = row.get("service_type")
        if key in buckets:
            buckets[key].append(row)
        else:
            extra.append(row)
    groups = [
        {"key": key, "label": SERVICE_TYPE_LABELS[key], "rows": items}
        for key, items in buckets.items()
        if items
    ]
    if extra:
        groups.append({"key": "OTHER", "label": "Other", "rows": extra})
    return groups


@login_required
@role_required(*OPERATIONS_ROLES)
def tour_list(request):
    try:
        tours = TourService().list_presented()
    except DatabaseUnavailableError:
        messages.error(request, "Cannot reach MongoDB. Tours are unavailable.")
        tours = []
    except TourOpsError as extra:
        messages.error(request, extra.message)
        tours = []
    return render(
        request,
        "tours/list.html",
        {
            "page_title": "Tours",
            "page_heading": "Departures",
            "tours": tours,
        },
    )


@login_required
@role_required(*OPERATIONS_ROLES)
@require_http_methods(["GET", "POST"])
def tour_create(request):
    try:
        choices = _package_choices()
    except DatabaseUnavailableError:
        return _unavailable(request)
    initial = {}
    package_id = (request.GET.get("package_id") or "").strip()
    if request.method == "GET" and package_id:
        try:
            initial = initial_from_package(PackageService().get_presented(package_id, include_extras=False))
        except (NotFoundError, TourOpsError):
            messages.error(request, "Package not found.")
    form = TourForm(request.POST or None, initial=initial or None, package_choices=choices)
    if request.method == "POST" and form.is_valid():
        try:
            tour = TourService().create(actor_id=get_session_user(request)["id"], **_form_payload(form))
        except DatabaseUnavailableError:
            return _unavailable(request)
        except TourOpsError as extra:
            messages.error(request, extra.message)
        else:
            messages.success(request, f"Created {tour['tour_code']}.")
            return redirect("tours:detail", id=str(tour["_id"]))
    return render(
        request,
        "tours/form.html",
        {
            "form": form,
            "page_title": "New tour",
            "page_heading": "New departure",
            "submit_label": "Save tour",
        },
    )


@login_required
@role_required(*OPERATIONS_ROLES)
def tour_detail(request, id):
    tab = (request.GET.get("tab") or "overview").strip().lower()
    allowed = {"overview", "bookings", "travelers", "services", "reservations", "rooming", "expenses", "profit", "activity"}
    if tab not in allowed:
        tab = "overview"
    try:
        record = TourService().get_presented(id)
        record["planned_ops"] = SupplierReservationService().match_planned(
            record.get("services") or [],
            record.get("reservations") or [],
        )
        record["reservation_groups"] = _reservation_groups(record.get("reservations") or [])
    except DatabaseUnavailableError:
        return _unavailable(request)
    except TourOpsError:
        messages.error(request, "Tour not found.")
        return redirect("tours:list")
    if tab == "rooming":
        return redirect("supplier_reservations:rooming", tour_id=id)
    return render(
        request,
        "tours/detail.html",
        {
            "page_title": record["name"],
            "page_heading": record["name"],
            "crumbs": [
                {"label": "Tours", "url": reverse("tours:list")},
                {"label": record["code"], "url": ""},
            ],
            "record": record,
            "tab": tab,
        },
    )


@login_required
@role_required(*OPERATIONS_ROLES)
def tour_rooming(request, id):
    return redirect("supplier_reservations:rooming", tour_id=id)


@login_required
@role_required(*OPERATIONS_ROLES)
@require_http_methods(["GET", "POST"])
def tour_edit(request, id):
    service = TourService()
    try:
        record = service.get_presented(id, include_extras=False)
        choices = _package_choices()
    except DatabaseUnavailableError:
        return _unavailable(request)
    except TourOpsError:
        messages.error(request, "Tour not found.")
        return redirect("tours:list")
    form = TourForm(
        request.POST or None,
        initial=initial_from_tour(record),
        package_choices=choices,
        include_status=True,
    )
    if request.method == "POST" and form.is_valid():
        try:
            service.update(id, actor_id=get_session_user(request)["id"], **_form_payload(form))
        except DatabaseUnavailableError:
            return _unavailable(request)
        except TourOpsError as extra:
            messages.error(request, extra.message)
        else:
            messages.success(request, f"Updated {record['code']}.")
            return redirect("tours:detail", id=id)
    return render(
        request,
        "tours/form.html",
        {
            "form": form,
            "page_title": f"Edit {record['name']}",
            "page_heading": f"Edit {record['name']}",
            "submit_label": "Save changes",
            "record": record,
        },
    )


@login_required
@role_required(*OPERATIONS_ROLES)
@require_POST
def tour_delete(request, id):
    try:
        TourService().soft_delete(id, actor_id=get_session_user(request)["id"])
    except DatabaseUnavailableError:
        return _unavailable(request)
    except TourOpsError as extra:
        messages.error(request, extra.message)
        return redirect("tours:detail", id=id)
    messages.success(request, "Tour deleted.")
    return redirect("tours:list")


@login_required
@role_required(*OPERATIONS_ROLES)
def availability(request):
    try:
        tours = TourService().availability()
    except DatabaseUnavailableError:
        messages.error(request, "Cannot reach MongoDB. Availability is unavailable.")
        tours = []
    except TourOpsError as extra:
        messages.error(request, extra.message)
        tours = []
    return render(
        request,
        "tours/availability.html",
        {
            "page_title": "Availability",
            "page_heading": "Seat availability",
            "tours": tours,
        },
    )
