from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.bookings.forms import BookingForm
from apps.bookings.services import BookingService
from apps.customers.services import CustomerService
from apps.tours.services import TourService
from core.access import OPERATIONS_ROLES
from core.exceptions import DatabaseUnavailableError, TourOpsError
from core.permissions import get_session_user, login_required, role_required


def _unavailable(request):
    messages.error(request, "Cannot reach MongoDB. Check MONGODB_URI and that MongoDB is running.")
    return redirect("bookings:list")


def _travelers_from_post(post) -> list[dict]:
    people = []
    for index in range(8):
        first = (post.get(f"traveler_{index}_first") or "").strip()
        last = (post.get(f"traveler_{index}_last") or "").strip()
        if not first and not last:
            continue
        people.append(
            {
                "first_name": first,
                "last_name": last,
                "passport_number": (post.get(f"traveler_{index}_passport") or "").strip(),
                "nationality": (post.get(f"traveler_{index}_nationality") or "").strip(),
            }
        )
    return people


@login_required
@role_required(*OPERATIONS_ROLES)
def booking_list(request):
    try:
        bookings = BookingService().list_presented()
    except DatabaseUnavailableError:
        messages.error(request, "Cannot reach MongoDB. Bookings are unavailable.")
        bookings = []
    return render(
        request,
        "bookings/list.html",
        {"page_title": "Bookings", "page_heading": "Bookings", "bookings": bookings},
    )


@login_required
@role_required(*OPERATIONS_ROLES)
@require_http_methods(["GET", "POST"])
def booking_create(request):
    try:
        customers = CustomerService().list_options()
        tours = [(row["id"], f"{row['name']} · {row['available']} seats left") for row in TourService().list_presented()]
    except DatabaseUnavailableError:
        return _unavailable(request)
    initial = {}
    if request.GET.get("tour_id"):
        initial["tour_id"] = request.GET.get("tour_id")
    if request.GET.get("customer_id"):
        initial["customer_id"] = request.GET.get("customer_id")
    form = BookingForm(request.POST or None, initial=initial or None, customer_choices=customers, tour_choices=tours)
    if request.method == "POST" and form.is_valid():
        try:
            booking = BookingService().create(
                actor_id=get_session_user(request)["id"],
                customer_id=form.cleaned_data["customer_id"],
                tour_id=form.cleaned_data["tour_id"],
                travelers=_travelers_from_post(request.POST),
                notes=form.cleaned_data.get("notes"),
            )
        except DatabaseUnavailableError:
            return _unavailable(request)
        except TourOpsError as extra:
            messages.error(request, extra.message)
        else:
            messages.success(request, f"Created {booking['booking_number']} as pending.")
            return redirect("bookings:detail", id=str(booking["_id"]))
    return render(
        request,
        "bookings/create.html",
        {"form": form, "page_title": "New booking", "page_heading": "New booking", "traveler_rows": range(4)},
    )


@login_required
@role_required(*OPERATIONS_ROLES)
def booking_detail(request, id):
    try:
        record = BookingService().get_presented(id)
    except DatabaseUnavailableError:
        return _unavailable(request)
    except TourOpsError:
        messages.error(request, "Booking not found.")
        return redirect("bookings:list")
    return render(
        request,
        "bookings/detail.html",
        {
            "page_title": record["number"],
            "page_heading": record["number"],
            "crumbs": [{"label": "Bookings", "url": reverse("bookings:list")}, {"label": record["number"], "url": ""}],
            "record": record,
        },
    )


@login_required
@role_required(*OPERATIONS_ROLES)
@require_POST
def booking_confirm(request, id):
    try:
        BookingService().confirm(id, actor_id=get_session_user(request)["id"])
    except DatabaseUnavailableError:
        return _unavailable(request)
    except TourOpsError as extra:
        messages.error(request, extra.message)
        return redirect("bookings:detail", id=id)
    messages.success(request, "Booking confirmed. Tour seats updated.")
    return redirect("bookings:detail", id=id)


@login_required
@role_required(*OPERATIONS_ROLES)
@require_POST
def booking_cancel(request, id):
    try:
        BookingService().cancel(id, actor_id=get_session_user(request)["id"])
    except DatabaseUnavailableError:
        return _unavailable(request)
    except TourOpsError as extra:
        messages.error(request, extra.message)
        return redirect("bookings:detail", id=id)
    messages.success(request, "Booking cancelled. Confirmed seats were returned to the tour.")
    return redirect("bookings:detail", id=id)
