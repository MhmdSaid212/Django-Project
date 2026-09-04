from datetime import datetime, timezone, timedelta
from decimal import Decimal

from django.shortcuts import redirect
from django.urls import reverse

from apps.bookings.services import BookingService
from apps.tours.repositories import TourRepository
from apps.payments.repositories import PaymentRepository

from core.access import dashboard_for_role
from core.constants import UserRole
from core.permissions import get_session_user, login_required, role_required
from core.wireframes import wireframe
from apps.invoices.repositories import InvoiceRepository
from apps.refunds.repositories import RefundRepository
from apps.supplier_payments.repositories import SupplierPaymentRepository
from core.constants import RefundStatus
from apps.expenses.repositories import ExpenseRepository


def _decimal(value):
    if value is None:
        return Decimal("0")

    if hasattr(value, "to_decimal"):
        return value.to_decimal()

    return Decimal(str(value))


def _dashboard(request, title: str):

    booking_service = BookingService()
    tour_repository = TourRepository()
    payment_repository = PaymentRepository()
    invoice_repository = InvoiceRepository()
    refund_repository = RefundRepository()
    supplier_payment_repository = SupplierPaymentRepository()
    expense_repository = ExpenseRepository()

    bookings = booking_service.list_items()
    tours = tour_repository.list_tours()
    tour_costs = tour_repository.costs_by_tour()
    today = datetime.now(timezone.utc).date()
    selected_month = int(request.GET.get("month", today.month))
    selected_year = int(request.GET.get("year", today.year))

    period_start = datetime(
        selected_year,
        selected_month,
        1,
        tzinfo=timezone.utc,
    ).date()

    if selected_month == 12:
        period_end = datetime(
            selected_year + 1,
            1,
            1,
            tzinfo=timezone.utc,
        ).date()
    else:
        period_end = datetime(
            selected_year,
            selected_month + 1,
            1,
            tzinfo=timezone.utc,
        ).date()

    period_end = period_end - timedelta(days=1)
    # ---------------------------------------------------------
    # BOOKING COUNTS
    # ---------------------------------------------------------

    active_bookings = [
        booking
        for booking in bookings
        if booking.get("booking_status") not in {
            "CANCELLED",
            "COMPLETED",
        }
    ]

    pending_bookings = [
        booking
        for booking in bookings
        if booking.get("booking_status") == "PENDING"
    ]

    confirmed_bookings = [
        booking
        for booking in bookings
        if booking.get("booking_status") == "CONFIRMED"
    ]

    completed_bookings = [
        booking
        for booking in bookings
        if booking.get("booking_status") == "COMPLETED"
    ]

    # ---------------------------------------------------------
    # REVENUE
    # ---------------------------------------------------------

    revenue = sum(
    (
        _decimal(booking.get("pricing", {}).get("total_amount", 0))
        for booking in bookings
        if booking.get("booking_status") != "CANCELLED"
        and booking.get("booking_date")
        and period_start <= booking["booking_date"].date() <= period_end
    ),
    Decimal("0"),
)

        # ---------------------------------------------------------
    # CUSTOMER OUTSTANDING
    # ---------------------------------------------------------

    customer_outstanding = Decimal("0")

    for booking in bookings:
        if booking.get("booking_status") == "CANCELLED":
            continue

        booking_date = booking.get("booking_date")

        if not booking_date or booking_date.date() > period_end:
            continue

        total = _decimal(
            booking.get("pricing", {}).get("total_amount", 0)
        )

        payments = payment_repository.find_for_booking(
            booking["_id"]
        )

        paid = sum(
            (
                _decimal(payment.get("amount", 0))
                for payment in payments
                if payment.get("created_at")
                and payment["created_at"].date() <= period_end
            ),
            Decimal("0"),
        )

        customer_outstanding += max(
            Decimal("0"),
            total - paid,
        )

    # ---------------------------------------------------------
    # UPCOMING TOURS
    # ---------------------------------------------------------

    upcoming_tours = []

    for tour in tours:

        start_date = tour.get("start_date")

        if not start_date:
            continue

        if start_date.date() < today:
            continue

        capacity = tour.get("capacity", 0) or 0
        booked = tour.get("booked_seats", 0) or 0

        available = max(
            0,
            capacity - booked,
        )

        if capacity and booked >= capacity:
            status = "FULLY_BOOKED"
        elif capacity and booked / capacity >= 0.8:
            status = "NEAR_CAPACITY"
        else:
            status = "AVAILABLE"

        upcoming_tours.append({
            "id": str(tour["_id"]),
            "name": tour.get("name", "—"),
            "city": tour.get(
                "destination",
                {}
            ).get(
                "city",
                "—",
            ),
            "country": tour.get(
                "destination",
                {}
            ).get(
                "country",
                "—",
            ),
            "start": start_date.strftime(
                "%d %b %Y"
            ),
            "booked": booked,
            "capacity": capacity,
            "available": available,
            "status": status,
            "projected": (
            _decimal(tour.get("selling_price_per_person", 0)) * booked
            - _decimal(tour_costs.get(str(tour["_id"]), 0))
        ),
        })

    upcoming_tours.sort(
        key=lambda tour: datetime.strptime(
            tour["start"],
            "%d %b %Y",
        )
    )

    upcoming_tours = upcoming_tours[:4]

    # ---------------------------------------------------------
    # BOOKING PIPELINE
    # ---------------------------------------------------------

    pipeline = {
        "pending": len(pending_bookings),
        "confirmed": len(confirmed_bookings),
        "progress": 0,
        "completed": len(completed_bookings),
    }

    # ---------------------------------------------------------
    # FINANCE
    # ---------------------------------------------------------

    money_in = sum(
    (
        _decimal(payment.get("amount", 0))
        for booking in bookings
        for payment in payment_repository.find_for_booking(booking["_id"])
        if payment.get("created_at")
        and period_start <= payment["created_at"].date() <= period_end
    ),
    Decimal("0"),
)

    money_out = Decimal("0")

    supplier_payables = Decimal("0")

    for expense in expense_repository.list_expenses():

        expense_date = expense.get("expense_date")

        if not expense_date or expense_date.date() > period_end:
            continue

        amount = _decimal(expense.get("amount", 0))

        payments = expense_repository.list_payments_for_expense(
            expense["_id"]
        )

        paid = sum(
            (
                _decimal(payment.get("amount", 0))
                for payment in payments
                if payment.get("payment_date")
                and payment["payment_date"].date() <= period_end
            ),
            Decimal("0"),
        )

        supplier_payables += max(
            Decimal("0"),
            amount - paid,
        )

    # ---------------------------------------------------------
    # ATTENTION CENTER
    # ---------------------------------------------------------

    near_capacity = [
        tour
        for tour in tours
        if (
            (tour.get("capacity") or 0) > 0
            and (
                (tour.get("booked_seats") or 0)
                / tour.get("capacity")
            ) >= 0.8
        )
    ]

    overdue_invoices = [
    invoice
    for invoice in invoice_repository.list_invoices()
    if invoice.get("due_date")
    and invoice.get("due_date").date() < today
    and invoice.get("status") not in {"PAID", "CANCELLED"}
]
    
    pending_refunds = refund_repository.list_refunds(
        status=RefundStatus.PENDING.value
    )
  
    supplier_payments = [
        payment
        for payment in supplier_payment_repository.list_payments()
        if payment.get("payment_date")
        and payment.get("payment_date").date() <= today
    ]

    attention = {
        "overdue_invoices": len(overdue_invoices),
        "refunds": len(pending_refunds),
        "near_capacity": len(near_capacity),
        "supplier_payments": len(supplier_payments),
    }

    # ---------------------------------------------------------
    # RECENT ACTIVITY
    # ---------------------------------------------------------

    recent_bookings = sorted(
        bookings,
        key=lambda booking: booking.get(
            "updated_at"
        ) or booking.get(
            "created_at"
        ) or datetime.min.replace(
            tzinfo=timezone.utc
        ),
        reverse=True,
    )[:5]

    activity = []

    for booking in recent_bookings:

        number = booking.get(
            "booking_number",
            "Booking",
        )

        status = booking.get(
            "booking_status",
            "",
        )

        activity.append({
            "who": "Travel Agent",
            "text": f"{status.title()} booking {number}",
            "time": (
                booking.get("updated_at")
                or booking.get("created_at")
            ).strftime("%d %b %Y · %H:%M")
            if (
                booking.get("updated_at")
                or booking.get("created_at")
            )
            else "—",
        })

        # ---------------------------------------------------------
    # KPI DELTAS
    # ---------------------------------------------------------

    if selected_month == 1:
        previous_month = 12
        previous_year = selected_year - 1
    else:
        previous_month = selected_month - 1
        previous_year = selected_year

    previous_start = datetime(
        previous_year,
        previous_month,
        1,
        tzinfo=timezone.utc,
    ).date()

    if previous_month == 12:
        previous_end = datetime(
            previous_year + 1,
            1,
            1,
            tzinfo=timezone.utc,
        ).date()
    else:
        previous_end = datetime(
            previous_year,
            previous_month + 1,
            1,
            tzinfo=timezone.utc,
        ).date()

    previous_end -= timedelta(days=1)

    def percentage_delta(current, previous):
        current = _decimal(current)
        previous = _decimal(previous)

        if previous == 0:
            return 0 if current == 0 else 100

        return float(
            ((current - previous) / abs(previous)) * 100
        )

    previous_revenue = sum(
        (
            _decimal(
                booking.get("pricing", {}).get(
                    "total_amount", 0
                )
            )
            for booking in bookings
            if booking.get("booking_status") != "CANCELLED"
            and booking.get("booking_date")
            and previous_start
            <= booking["booking_date"].date()
            <= previous_end
        ),
        Decimal("0"),
    )

    previous_money_in = sum(
        (
            _decimal(payment.get("amount", 0))
            for booking in bookings
            for payment in payment_repository.find_for_booking(
                booking["_id"]
            )
            if payment.get("created_at")
            and previous_start
            <= payment["created_at"].date()
            <= previous_end
        ),
        Decimal("0"),
    )

    monthly_expenses = sum(
        (
            _decimal(expense.get("amount", 0))
            for expense in expense_repository.list_expenses()
            if expense.get("expense_date")
            and period_start
            <= expense["expense_date"].date()
            <= period_end
        ),
        Decimal("0"),
    )

    previous_expenses = sum(
        (
            _decimal(expense.get("amount", 0))
            for expense in expense_repository.list_expenses()
            if expense.get("expense_date")
            and previous_start
            <= expense["expense_date"].date()
            <= previous_end
        ),
        Decimal("0"),
    )

    monthly_profit = money_in - monthly_expenses
    previous_profit = previous_money_in - previous_expenses

    current_active = sum(
        1
        for booking in bookings
        if booking.get("booking_status")
        not in {"CANCELLED", "COMPLETED"}
        and booking.get("booking_date")
        and period_start
        <= booking["booking_date"].date()
        <= period_end
    )

    previous_active = sum(
        1
        for booking in bookings
        if booking.get("booking_status")
        not in {"CANCELLED", "COMPLETED"}
        and booking.get("booking_date")
        and previous_start
        <= booking["booking_date"].date()
        <= previous_end
    )


    previous_customer_outstanding = Decimal("0")

    for booking in bookings:
        if booking.get("booking_status") == "CANCELLED":
            continue

        booking_date = booking.get("booking_date")

        if not booking_date or booking_date.date() > previous_end:
            continue

        total = _decimal(
            booking.get("pricing", {}).get("total_amount", 0)
        )

        payments = payment_repository.find_for_booking(
            booking["_id"]
        )

        paid = sum(
            (
                _decimal(payment.get("amount", 0))
                for payment in payments
                if payment.get("created_at")
                and payment["created_at"].date() <= previous_end
            ),
            Decimal("0"),
        )

        previous_customer_outstanding += max(
            Decimal("0"),
            total - paid,
        )

    previous_supplier_payables = Decimal("0")

    for expense in expense_repository.list_expenses():

        expense_date = expense.get("expense_date")

        if not expense_date or expense_date.date() > previous_end:
            continue

        amount = _decimal(expense.get("amount", 0))

        payments = expense_repository.list_payments_for_expense(
            expense["_id"]
        )

        paid = sum(
            (
                _decimal(payment.get("amount", 0))
                for payment in payments
                if payment.get("payment_date")
                and payment["payment_date"].date() <= previous_end
            ),
            Decimal("0"),
        )

        previous_supplier_payables += max(
            Decimal("0"),
            amount - paid,
        )


    kpis = {
        "revenue": revenue,
        "revenue_delta": percentage_delta(
            revenue,
            previous_revenue,
        ),
        "ar": customer_outstanding,
        "ar_delta": percentage_delta(
        customer_outstanding,
        previous_customer_outstanding,
    ),
        "ap": supplier_payables,
        "ap_delta": percentage_delta(
            supplier_payables,
            previous_supplier_payables,
        ),
        "active_bookings": len(active_bookings),
        "active_bookings_delta": percentage_delta(
            current_active,
            previous_active,
        ),
        "upcoming": len(upcoming_tours),
        "profit": monthly_profit,
        "profit_delta": percentage_delta(
            monthly_profit,
            previous_profit,
        ),
    }

    # ---------------------------------------------------------
    # DASHBOARD MODEL
    # ---------------------------------------------------------
    months = [
    (1, "January"),
    (2, "February"),
    (3, "March"),
    (4, "April"),
    (5, "May"),
    (6, "June"),
    (7, "July"),
    (8, "August"),
    (9, "September"),
    (10, "October"),
    (11, "November"),
    (12, "December"),
]

    years = list(range(today.year - 2, today.year + 1))








    dashboard_data = {
        "kpis": kpis,
        "pipeline": pipeline,
        "money_in": money_in,
        "money_out": money_out,
        "tours": upcoming_tours,
        "activity": activity,
        "attention": attention,
        "unread": 0,
    }

    return wireframe(
        request,
        "dashboard/command.html",
        title,
        heading="Operations command center",
        lead="Here’s what needs attention across bookings, finance, and upcoming tours.",
        m=dashboard_data,
        months=months,
        years=years,
        selected_month=selected_month,
        selected_year=selected_year,
    )


@login_required
def home(request):
    user = get_session_user(request)
    return redirect(
        reverse(
            dashboard_for_role(
                user["role"]
            )
        )
    )


@login_required
@role_required(
    UserRole.TRAVEL_AGENT,
    UserRole.OWNER_ADMIN,
)
def agent(request):
    return _dashboard(
        request,
        "Agent dashboard",
    )


@login_required
@role_required(
    UserRole.ACCOUNTANT,
    UserRole.OWNER_ADMIN,
)
def accountant(request):
    return _dashboard(
        request,
        "Accountant dashboard",
    )


@login_required
@role_required(
    UserRole.OWNER_ADMIN,
)
def owner(request):
    return _dashboard(
        request,
        "Owner dashboard",
    )

