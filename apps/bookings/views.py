from apps.tours.repositories import TourRepository
from core.constants import UserRole
from core.exceptions import NotFoundError, TourOpsError, ValidationError
from core.permissions import login_required, role_required
from core.wireframes import record, wireframe

from core.constants import UserRole
from core.permissions import login_required, role_required
from core.wireframes import record, wireframe

from apps.bookings.services import BookingService
from apps.payments.repositories import PaymentRepository
from decimal import Decimal
from datetime import datetime, timezone
from django.shortcuts import redirect
from apps.customers.repositories import CustomerRepository


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def booking_list(request):

    service = BookingService()

    # --------------------------------------------------
    # Get ALL bookings
    # --------------------------------------------------

    all_bookings = service.list_items()

    # --------------------------------------------------
    # Global statistics
    # --------------------------------------------------

    total_bookings = len(all_bookings)

    confirmed_bookings = sum(
        1
        for booking in all_bookings
        if booking.get("booking_status") == "CONFIRMED"
    )

    pending_bookings = sum(
        1
        for booking in all_bookings
        if booking.get("booking_status") == "PENDING"
    )

    # --------------------------------------------------
    # Prepare booking data
    # --------------------------------------------------

    for booking in all_bookings:

        booking["number"] = booking.get(
            "booking_number",
            ""
        )

        # Customer
        customer = service.customer_repository.find_by_id(
            str(booking["customer_id"])
        )

        booking["customer"] = (
            f'{customer.get("first_name", "")} '
            f'{customer.get("last_name", "")}'
            if customer
            else "—"
        )

        # Tour
        tour = service.tour_repository.find_by_id(
            str(booking["tour_id"])
        )

        booking["product"] = (
            tour.get("name", "—")
            if tour
            else "—"
        )

        # Destination
        booking["destination"] = (
            f'{tour.get("destination", {}).get("city", "")}, '
            f'{tour.get("destination", {}).get("country", "")}'
            if tour
            else "—"
        )

        # Travel date
        booking["travel_date"] = (
            tour.get("start_date")
            if tour and tour.get("start_date")
            else None
        )

        booking["dates"] = (
            booking["travel_date"].strftime("%b %d, %Y")
            if booking["travel_date"]
            else "—"
        )

        # Travelers
        booking["travelers"] = booking.get(
            "travelers_count",
            0
        )

        # Total
        booking["total"] = booking.get(
            "pricing", {}
        ).get(
            "total_amount",
            0
        )

        # Status
        booking["status"] = booking.get(
            "booking_status",
            ""
        )

    # --------------------------------------------------
    # Upcoming revenue
    # --------------------------------------------------

    today = datetime.now(timezone.utc).date()

    upcoming_revenue = Decimal("0.00")

    for booking in all_bookings:

        travel_date = booking.get("travel_date")

        if not travel_date:
            continue

        if (
            travel_date.date() >= today
            and booking["status"] != "CANCELLED"
        ):

            amount = booking.get("total", 0)

            if hasattr(amount, "to_decimal"):
                amount = amount.to_decimal()
            else:
                amount = Decimal(str(amount))

            upcoming_revenue += amount

    # --------------------------------------------------
    # Status filter
    # --------------------------------------------------

    selected_status = request.GET.get("status")

    if selected_status:
        bookings = [
            booking
            for booking in all_bookings
            if booking["status"] == selected_status
        ]
    else:
        bookings = all_bookings

    # --------------------------------------------------
    # Pagination
    # --------------------------------------------------

    page_size = 5

    try:
        current_page = int(
            request.GET.get("page", 1)
        )
    except (TypeError, ValueError):
        current_page = 1

    total_filtered = len(bookings)

    total_pages = max(
        1,
        (total_filtered + page_size - 1) // page_size
    )

    current_page = max(
        1,
        min(current_page, total_pages)
    )

    start_index = (
        current_page - 1
    ) * page_size

    end_index = start_index + page_size

    bookings = bookings[
        start_index:end_index
    ]

    showing_start = (
        start_index + 1
        if total_filtered
        else 0
    )

    showing_end = min(
        end_index,
        total_filtered
    )

    # --------------------------------------------------
    # Context
    # --------------------------------------------------

    context = {
        "bookings": bookings,

        # Global stats
        "total_bookings": total_bookings,
        "confirmed_bookings": confirmed_bookings,
        "pending_bookings": pending_bookings,
        "upcoming_revenue": upcoming_revenue,

        # Filters
        "current_status": selected_status or "ALL",

        # Pagination
        "current_page": current_page,
        "total_pages": total_pages,
        "showing_start": showing_start,
        "showing_end": showing_end,
        "total_filtered": total_filtered,
    }

    return wireframe(
        request,
        "bookings/list.html",
        "Bookings",
        heading="Bookings",
        **context,
    )


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def booking_create(request):

    service = BookingService()

    customer_repository = CustomerRepository()
    tour_repository = TourRepository()

    # Load active customers
    customer_documents = customer_repository.find_all(
        limit=100,
        status="ACTIVE",
    )

    customers = []

    for customer in customer_documents:
        customers.append({
            "id": str(customer["_id"]),
            "name": (
                f'{customer.get("first_name", "")} '
                f'{customer.get("last_name", "")}'
            ).strip(),
            "number": customer.get("customer_number", ""),
            "city": customer.get("city", ""),
        })

    # Load available tours
    tour_documents = tour_repository.list_tours(
        {"status": "AVAILABLE"}
    )

    tours = []

    for tour in tour_documents:

        capacity = tour.get("capacity", 0)
        booked_seats = tour.get("booked_seats", 0)
        held_seats = tour.get("held_seats", 0)

        available_seats = (
            capacity
            - booked_seats
            - held_seats
        )

        if available_seats <= 0:
            continue

        destination = tour.get(
            "destination",
            {}
        )

        price = tour.get(
            "selling_price_per_person",
            0,
        )

        if hasattr(price, "to_decimal"):
            price = price.to_decimal()

        tours.append({
            "id": str(tour["_id"]),
            "name": tour.get("name", ""),
            "price": price,
            "start_date": (
                tour["start_date"].strftime("%b %d, %Y")
                if tour.get("start_date")
                else ""
            ),
            "end_date": (
                tour["end_date"].strftime("%b %d, %Y")
                if tour.get("end_date")
                else ""
            ),
            "city": destination.get("city", ""),
            "country": destination.get("country", ""),
            "capacity": capacity,
            "available_seats": available_seats,
        })

    if request.method == "POST":

        try:
            customer_id = request.POST.get("customer_id")
            tour_id = request.POST.get("tour_id")

            travelers_count = int(
                request.POST.get(
                    "travelers_count",
                    0,
                )
            )

            travelers = []

            for i in range(travelers_count):

                travelers.append({
                    "first_name": request.POST.get(
                        f"traveler_{i}_first_name",
                        "",
                    ).strip(),

                    "last_name": request.POST.get(
                        f"traveler_{i}_last_name",
                        "",
                    ).strip(),

                    "passport_number": request.POST.get(
                        f"traveler_{i}_passport",
                        "",
                    ).strip(),

                    "type": request.POST.get(
                        f"traveler_{i}_type",
                        "ADULT",
                    ),
                })

            unit_price = Decimal(
                request.POST.get(
                    "unit_price",
                    "0",
                )
            )

            discount = Decimal(
                request.POST.get(
                    "discount",
                    "0",
                )
            )

            tax_rate = Decimal(
                request.POST.get(
                    "tax_rate",
                    "0",
                )
            )

            subtotal = (
                unit_price * travelers_count
            )

            discount_amount = min(
                discount,
                subtotal,
            )

            taxable_amount = (
                subtotal - discount_amount
            )

            tax_amount = (
                taxable_amount
                * tax_rate
                / Decimal("100")
            )

            total_amount = (
                taxable_amount + tax_amount
            )

            pricing = {
                "unit_price": unit_price,
                "subtotal": subtotal,
                "discount_type": "FIXED",
                "discount_value": discount,
                "discount_amount": discount_amount,
                "discount_reason": None,
                "discount_applied_by": None,
                "taxable_amount": taxable_amount,
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "total_amount": total_amount,
                "tax_id": None,
            }

            booking = service.create(
                {
                    "customer_id": customer_id,
                    "tour_id": tour_id,
                    "travelers_count": travelers_count,
                    "travelers": travelers,
                    "pricing": pricing,
                    "notes": request.POST.get(
                        "notes",
                        "",
                    ).strip(),
                }
            )

            return redirect(
                "bookings:detail",
                id=booking["booking_number"],
            )

        except (
            ValidationError,
            NotFoundError,
            TourOpsError,
            ValueError,
            TypeError,
        ) as exc:

            return wireframe(
                request,
                "bookings/create.html",
                "Create booking",
                heading="New booking",
                customers=customers,
                tours=tours,
                error=str(exc),
            )

    return wireframe(
        request,
        "bookings/create.html",
        "Create booking",
        heading="New booking",
        customers=customers,
        tours=tours,
    )


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def booking_detail(request, id):

    service = BookingService()

    bookings = service.list_items()

    row = next(
        (
            booking
            for booking in bookings
            if booking.get("booking_number") == id
        ),
        None,
    )

    if not row:
        return wireframe(
            request,
            "bookings/detail.html",
            "Booking not found",
            heading="Booking not found",
        )

    # Booking number
    row["number"] = row.get("booking_number", "")

    # Customer
    customer = service.customer_repository.find_by_id(
        str(row["customer_id"])
    )

    row["customer"] = (
        f'{customer.get("first_name", "")} {customer.get("last_name", "")}'
        if customer
        else "—"
    )

    # Tour
    tour = service.tour_repository.find_by_id(
        str(row["tour_id"])
    )

    if tour:
        row["tour"] = tour.get("name", "—")
        row["product"] = tour.get("name", "—")

        destination = tour.get("destination", {})

        row["destination"] = (
            f'{destination.get("city", "")}, '
            f'{destination.get("country", "")}'
        )

        row["dates"] = (
            f'{tour.get("start_date").strftime("%b %d, %Y")} – '
            f'{tour.get("end_date").strftime("%b %d, %Y")}'
            if tour.get("start_date") and tour.get("end_date")
            else "—"
        )
    else:
        row["tour"] = "—"
        row["destination"] = "—"
        row["dates"] = "—"

    # Travelers
    row["traveler_count"] = len(row.get("travelers", []))

    # Booking total
    pricing = row.get("pricing", {})

    row["total"] = pricing.get("total_amount", 0)
    payment_repository = PaymentRepository()

    payments = payment_repository.find_for_booking(row["_id"])

    row["paid"] = sum(
    (
        payment.get("amount", 0).to_decimal()
        if hasattr(payment.get("amount", 0), "to_decimal")
        else Decimal(str(payment.get("amount", 0)))
        for payment in payments
    ),
    Decimal("0"),
)

    row["remaining"] = max(
        Decimal("0"),
        Decimal(str(row["total"])) - row["paid"],
    )

    row["pay"] = row.get("payment_status", "UNPAID")
    # Status
    row["status"] = row.get("booking_status", "")

    # Notes
    row["notes"] = row.get("notes") or "No notes have been added to this booking yet."
    row["itinerary"] = row.get("itinerary", [])


    return wireframe(
        request,
        "bookings/detail.html",
        row["number"],
        heading=row["number"],
        crumbs=[
            {"label": "Bookings", "url": "/bookings/"},
            {"label": row["number"], "url": ""},
        ],
        record=row,
    )


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def booking_confirm(request, id):

    if request.method != "POST":
        return redirect("bookings:detail", id=id)

    service = BookingService()

    booking = next(
        (
            booking
            for booking in service.list_items()
            if booking.get("booking_number") == id
        ),
        None,
    )

    if not booking:
        raise NotFoundError("Booking not found.")

    service.confirm(str(booking["_id"]))

    return redirect(
        "bookings:detail",
        id=id,
    )


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def booking_cancel(request, id):

    if request.method != "POST":
        return redirect("bookings:detail", id=id)

    service = BookingService()

    booking = next(
        (
            booking
            for booking in service.list_items()
            if booking.get("booking_number") == id
        ),
        None,
    )

    if not booking:
        raise NotFoundError("Booking not found.")

    service.cancel(str(booking["_id"]))

    return redirect(
        "bookings:detail",
        id=id,
    )