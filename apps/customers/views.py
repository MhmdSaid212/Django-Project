from django.http import request

from apps import invoices
from apps.tours.repositories import TourRepository
from core.constants import UserRole
from core.permissions import (get_session_user,login_required,role_required,)
from core.wireframes import record, wireframe
from apps.customers.services import CustomerService
from datetime import datetime, timedelta
from apps.bookings.services import BookingService
from django.shortcuts import redirect, render
from apps.invoices.repositories import InvoiceRepository
from bson.decimal128 import Decimal128
from decimal import Decimal
from apps.payments.services import PaymentService
from apps.attachments.services import AttachmentService
from core.permissions import get_session_user
from apps.audit.services import AuditService

@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def customer_list(request):
    query = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip().upper() or None

    service = CustomerService()
    invoice_repository = InvoiceRepository()

    customers = service.list_items(
    query=query or None,
    status=status,
)

    all_customers = service.list_items()

    rows = []
    total_customers = 0
    active_customers = 0
    outstanding_customers = 0
    outstanding_ar = 0

    for customer in customers:
        first = customer.get("first_name", "")
        last = customer.get("last_name", "")
        name = f"{first} {last}".strip()


        total_customers = len(all_customers)

        active_customers = sum(
            1 for customer in all_customers
            if customer.get("status") == "ACTIVE"
        )

        invoices = invoice_repository.list_invoices(
            customer_id=str(customer["_id"])
        )

        balance = sum(
            (
                invoice.get("remaining_amount").to_decimal()
                if isinstance(invoice.get("remaining_amount"), Decimal128)
                else Decimal(str(invoice.get("remaining_amount", 0)))
            )
            for invoice in invoices
            if invoice.get("status") != "CANCELLED"
        )

        bookings = BookingService().list_items(
            customer_id=str(customer["_id"])
        )

        upcoming = None

        for booking in bookings:
            if booking.get("booking_status") == "CANCELLED":
                continue

            tour = TourRepository().find_by_id(
                str(booking["tour_id"])
            )

            if not tour:
                continue

            start_date = tour.get("start_date")

            if not start_date:
                continue

            if upcoming is None or start_date < upcoming["date"]:
                upcoming = {
                    "date": start_date,
                    "name": tour.get("name", "—"),
                }

        rows.append({
            "id": str(customer["_id"]),
            "number": customer.get("customer_number", ""),
            "first": first,
            "last": last,
            "name": name,
            "initials": (
                f"{first[:1]}{last[:1]}".upper()
                if first or last
                else "—"
            ),
            "email": customer.get("email", ""),
            "phone": customer.get("phone", ""),
            "status": customer.get("status", "INACTIVE"),
            "city": customer.get("address", {}).get("city", ""),
            "country": customer.get("address", {}).get("country", ""),
            "balance": balance,
            "upcoming": upcoming,
        })
        total_customers = len(rows)

        active_customers = sum(
                1 for row in rows
                if row["status"] == "ACTIVE"
            )

        outstanding_customers = sum(
                1 for row in rows
                if row["balance"] > 0
            )

        outstanding_ar = sum(
                row["balance"]
                for row in rows
            )
    return wireframe(
        request,
        "customers/list.html",
        "Customers",
        heading="Customers",
        customers=rows,
        total_customers=total_customers,
        active_customers=active_customers,
        outstanding_customers=outstanding_customers,
        outstanding_ar=outstanding_ar
    )


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def customer_search(request):
    query = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip().upper() or None
    has_balance = request.GET.get("has_balance") == "1"
    has_upcoming = request.GET.get("has_upcoming") == "1"
    recent = request.GET.get("recent") == "1"
    recent_cutoff = datetime.utcnow() - timedelta(days=30)

    service = CustomerService()
    invoice_repository = InvoiceRepository()
    tour_repository = TourRepository()
    booking_service = BookingService()

    customers = service.list_items(
        query=query or None,
        status=status,
    )

    rows = []

    for customer in customers:
        if recent:
            created_at = customer.get("created_at")

            if not created_at or created_at < recent_cutoff:
                continue


        first = customer.get("first_name", "")
        last = customer.get("last_name", "")
        name = f"{first} {last}".strip()
        
        invoices = invoice_repository.list_invoices(
            customer_id=str(customer["_id"])
        )

        balance = sum(
            (
                invoice.get("remaining_amount").to_decimal()
                if isinstance(invoice.get("remaining_amount"), Decimal128)
                else Decimal(str(invoice.get("remaining_amount", 0)))
            )
            for invoice in invoices
            if invoice.get("status") != "CANCELLED"
        )

        bookings = booking_service.list_items(
            customer_id=str(customer["_id"])
        )

        upcoming = None

        for booking in bookings:
            if booking.get("booking_status") == "CANCELLED":
                continue

            if not booking.get("tour_id"):
                continue

            tour = tour_repository.find_by_id(
                str(booking["tour_id"])
            )

            if not tour:
                continue

            start_date = tour.get("start_date")

            if not start_date:
                continue

            if upcoming is None or start_date < upcoming["date"]:
                upcoming = {
                    "date": start_date,
                    "name": tour.get("name", "—"),
                }

        # Has balance filter
        if has_balance and balance <= 0:
            continue

        if has_upcoming and upcoming is None:
            continue
        rows.append({
            "id": str(customer["_id"]),
            "number": customer.get("customer_number", ""),
            "first": first,
            "last": last,
            "name": name,
            "initials": (
                f"{first[:1]}{last[:1]}".upper()
                if first or last
                else "—"
            ),
            "email": customer.get("email", ""),
            "phone": customer.get("phone", ""),
            "status": customer.get("status", "INACTIVE"),
            "balance": balance,
            "upcoming": upcoming,
        })

    return render(
        request,
        "customers/_customer_rows.html",
        {"customers": rows},
    )



@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def customer_create(request):
    if request.method == "POST":
        date_of_birth = request.POST.get("date_of_birth") or None

        if date_of_birth:
            date_of_birth = datetime.fromisoformat(date_of_birth)

        data = {
            "first_name": request.POST.get("first_name", ""),
            "last_name": request.POST.get("last_name", ""),
            "email": request.POST.get("email", ""),
            "phone": request.POST.get("phone_full") or request.POST.get("phone", ""),
            "nationality": request.POST.get("nationality") or None,
            "address": {
                "country": request.POST.get("address_country", ""),
                "city": request.POST.get("address_city", ""),
                "street": request.POST.get("address_street") or None,
            },
            "passport": {
                "number": request.POST.get("passport_number") or None,
                "expiry_date": request.POST.get("passport_expiry_date") or None,
                "issuing_country": request.POST.get("passport_issuing_country") or None,
            },
            "emergency_contact": {
                "name": request.POST.get("emergency_contact_name") or None,
                "phone": (
                    request.POST.get("emergency_contact_phone")
                    or request.POST.get("emergency_contact_phone_full")
                    or None
                ),
                "relationship": request.POST.get("emergency_contact_relationship") or None,
            },
            "notes": request.POST.get("notes") or None,
        }

        service = CustomerService()

        try:
            customer = service.create(data, date_of_birth=date_of_birth)
            user = get_session_user(request)

            AuditService().create(
                user_id=user["id"],
                action="CUSTOMER_CREATED",
                entity_type="customer",
                entity_id=str(customer["_id"]),
                description=f"Customer {customer.get('first_name', '')} {customer.get('last_name', '')} was created.",
            )
            uploaded_file = request.FILES.get("document")
            print("FILES:", request.FILES)
            print("UPLOADED FILE:", uploaded_file)
            if uploaded_file:
                user = get_session_user(request)

                AttachmentService().upload_for_customer(
                    str(customer["_id"]),
                    uploaded_file,
                    category=request.POST.get("document_category", "OTHER") or "OTHER",
                    uploaded_by=user["id"],
                    notes=request.POST.get("document_notes") or None,
                )
        except ValueError as exc:
            record = {
                "first_name": request.POST.get("first_name", ""),
                "last_name": request.POST.get("last_name", ""),
                "status": request.POST.get("status", "ACTIVE"),
                "email": request.POST.get("email", ""),
                "phone": request.POST.get("phone", ""),
                "phone_full": request.POST.get("phone_full", ""),
                "date_of_birth": request.POST.get("date_of_birth", ""),
                "nationality": request.POST.get("nationality", ""),

                "address": {
                    "country": request.POST.get("address_country", ""),
                    "city": request.POST.get("address_city", ""),
                    "street": request.POST.get("address_street", ""),
                },

                "passport": {
                    "number": request.POST.get("passport_number", ""),
                    "expiry_date": request.POST.get("passport_expiry_date", ""),
                    "issuing_country": request.POST.get("passport_issuing_country", ""),
                },

                "emergency_contact": {
                    "name": request.POST.get("emergency_contact_name", ""),
                    "phone": request.POST.get("emergency_contact_phone", ""),
                    "phone_full": request.POST.get("emergency_contact_phone_full", ""),
                    "relationship": request.POST.get("emergency_contact_relationship", ""),
                },

                "notes": request.POST.get("notes", ""),
            }

            return wireframe(
                request,
                "customers/form.html",
                "Create customer",
                heading="New customer",
                error=str(exc),
                record=record,
            )

        return redirect("customers:detail", id=str(customer["_id"]))

    return wireframe(
        request,
        "customers/form.html",
        "Create customer",
        heading="New customer",
        record={
            "first_name": "",
            "last_name": "",
            "status": "ACTIVE",
            "email": "",
            "phone": "",
            "phone_full": "",
            "date_of_birth": "",
            "nationality": "",

            "address": {
                "country": "",
                "city": "",
                "street": "",
            },

            "passport": {
                "number": "",
                "expiry_date": "",
                "issuing_country": "",
            },

            "emergency_contact": {
                "name": "",
                "phone": "",
                "phone_full": "",
                "relationship": "",
            },

            "notes": "",
        },
    )


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def customer_detail(request, id):
    service = CustomerService()
    customer = service.get(id)

    if not customer:
        from django.http import Http404
        raise Http404("Customer not found")

    first = customer.get("first_name", "")
    last = customer.get("last_name", "")
    name = f"{first} {last}".strip()


    audit_service = AuditService()

    activities = [
        log
        for log in audit_service.list_items()
        if log.get("entity_type") == "customer"
        and str(log.get("entity_id")) == str(customer["_id"])
    ]


    attachment_service = AttachmentService()

    attachments = attachment_service.list_for_customer(
        str(customer["_id"])
    )
    # Get customer's bookings
    booking_service = BookingService()
    tour_repository = TourRepository()

    bookings = booking_service.list_items(
        customer_id=str(customer["_id"])
    )

    invoice_repository = InvoiceRepository()

    invoices = invoice_repository.list_invoices(
        customer_id=str(customer["_id"])
    )

    balance = sum(
    (
        invoice.get("remaining_amount").to_decimal()
        if isinstance(invoice.get("remaining_amount"), Decimal128)
        else Decimal(str(invoice.get("remaining_amount", 0)))
    )
    for invoice in invoices
    if invoice.get("status") != "CANCELLED"
)


    payment_service = PaymentService()

    payments = payment_service.list_items(
        customer_id=str(customer["_id"])
    )

    lifetime = sum(
        Decimal(payment.get("amount", "0"))
        for payment in payments
        if payment.get("status") == "COMPLETED"
    )

    invoice_rows = []

    for invoice in invoices:
        invoice_rows.append({
            "id": str(invoice["_id"]),
            "number": invoice.get("invoice_number", ""),
            "booking_number": invoice.get("booking_number", ""),
            "total": invoice.get("total_amount", 0),
            "paid": invoice.get("paid_amount", 0),
            "remaining": invoice.get("remaining_amount", 0),
            "status": invoice.get("status", ""),
        })

    payment_rows = []

    for payment in payments:
        payment_rows.append({
            "id": payment.get("id"),
            "number": payment.get("payment_number", ""),
            "invoice": payment.get("invoice_id", ""),
            "date": payment.get("payment_date"),
            "amount": payment.get("amount", 0),
            "method": payment.get("payment_method", ""),
            "status": payment.get("status", ""),
        })

    financial_timeline = []

    for invoice in invoices:
            financial_timeline.append({
                "type": "INVOICE",
                "date": invoice.get("issue_date") or invoice.get("created_at"),
                "title": f"Invoice {invoice.get('invoice_number', '')}",
                "description": "Invoice issued",
                "amount": invoice["total_amount"].to_decimal(),
            })

    for payment in payments:
            if payment.get("status") != "COMPLETED":
                continue

            financial_timeline.append({
                "type": "PAYMENT",
                "date": payment.get("payment_date") or payment.get("created_at"),
                "title": f"Payment {payment.get('payment_number', '')}",
                "description": "Payment received",
                "amount": payment.get("amount", 0),
            })

    financial_timeline.sort(
            key=lambda item: item.get("date") or datetime.min,
            reverse=True,
        )
    # Find upcoming trip
    upcoming = None

    for booking in bookings:
        if booking.get("booking_status") == "CANCELLED":
            continue

        if not booking.get("tour_id"):
            continue

        tour = tour_repository.find_by_id(
            booking["tour_id"]
        )

        if not tour or not tour.get("start_date"):
            continue

        start_date = tour["start_date"]

        if start_date >= datetime.now():
            if upcoming is None or start_date < upcoming:
                upcoming = start_date

    row = {
        "id": str(customer["_id"]),
        "number": customer.get("customer_number", ""),
        "first": first,
        "last": last,
        "name": name,
        "initials": (
            f"{first[:1]}{last[:1]}".upper()
            if first or last
            else "—"
        ),
        "email": customer.get("email", ""),
        "phone": customer.get("phone", ""),
        "status": customer.get("status", "INACTIVE"),
        "city": customer.get("address", {}).get("city", ""),
        "country": customer.get("address", {}).get("country", ""),
        "passport": customer.get("passport", {}).get("number"),
        "passport_expiry": customer.get("passport", {}).get("expiry_date"),
        "emergency": customer.get("emergency_contact", {}).get("name"),
        "date_of_birth": customer.get("date_of_birth"),
        "nationality": customer.get("nationality"),
        "address_country": customer.get("address", {}).get("country", ""),
        "address_city": customer.get("address", {}).get("city", ""),
        "address_street": customer.get("address", {}).get("street"),
        "passport_issuing_country": customer.get("passport", {}).get("issuing_country"),
        "emergency_phone": customer.get("emergency_contact", {}).get("phone"),
        "emergency_relationship": customer.get("emergency_contact", {}).get("relationship"),
        "notes": customer.get("notes"),

        # Real metrics
        "upcoming": upcoming,
        "balance": balance,
        "bookings": len(bookings),
        "lifetime": lifetime,
    }

    booking_rows = []

    for booking in bookings:
        tour = None

        if booking.get("tour_id"):
            tour = tour_repository.find_by_id(
                booking["tour_id"]
            )

        booking_rows.append({
            "id": str(booking["_id"]),
            "number": booking.get("booking_number", ""),
            "status": booking.get("booking_status", ""),
            "remaining": booking.get("pricing", {}).get("total_amount", 0),
            "product": tour.get("name", "—") if tour else "—",
            "dates": (
                f"{tour.get('start_date', '—')} → {tour.get('end_date', '—')}"
                if tour
                else "—"
            ),
        })

    return wireframe(
        request,
        "customers/detail.html",
        name,
        heading=name,
        crumbs=[
            {"label": "Customers", "url": "/customers/"},
            {"label": row["number"], "url": ""},
        ],
        record=row,
        bookings=booking_rows,
        invoices=invoice_rows,
        payments=payment_rows,
        attachments=attachments,
        customer_id=str(customer["_id"]),
        activities=activities,
        financial_timeline=financial_timeline,
        tab=request.GET.get("tab", "overview"),
    )


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def customer_edit(request, id):
    service = CustomerService()

    customer = service.get(id)

    if not customer:
        from django.http import Http404
        raise Http404("Customer not found")

    if request.method == "POST":
        date_of_birth = request.POST.get("date_of_birth") or None

        if date_of_birth:
            date_of_birth = datetime.fromisoformat(date_of_birth)

        data = {
            "first_name": request.POST.get("first_name", ""),
            "last_name": request.POST.get("last_name", ""),
            "email": request.POST.get("email", ""),
            "phone": (
                request.POST.get("phone_full")
                or request.POST.get("phone", "")
            ),
            "status": request.POST.get("status", "ACTIVE"),
            "date_of_birth": date_of_birth,
            "nationality": request.POST.get("nationality") or None,

            "address": {
                "country": request.POST.get("address_country", ""),
                "city": request.POST.get("address_city", ""),
                "street": request.POST.get("address_street") or None,
            },

            "passport": {
                "number": request.POST.get("passport_number") or None,
                "expiry_date": request.POST.get("passport_expiry_date") or None,
                "issuing_country": (
                    request.POST.get("passport_issuing_country")
                    or None
                ),
            },

            "emergency_contact": {
                "name": (
                    request.POST.get("emergency_contact_name")
                    or None
                ),
                "phone": (
                    request.POST.get("emergency_contact_phone")
                    or request.POST.get("emergency_contact_phone_full")
                    or None
                ),
                "relationship": (
                    request.POST.get("emergency_contact_relationship")
                    or None
                ),
            },

            "notes": request.POST.get("notes") or None,
        }

        try:
            customer = service.update(
                id,
                data,
            )

            user = get_session_user(request)

            AuditService().create(
                user_id=user["id"],
                action="CUSTOMER_UPDATED",
                entity_type="customer",
                entity_id=str(customer["_id"]),
                description=f"Customer {customer.get('first_name', '')} {customer.get('last_name', '')} was updated.",
            )

            uploaded_file = request.FILES.get("document")

            if uploaded_file:
                user = get_session_user(request)

                attachment = AttachmentService().upload_for_customer(
                    str(customer["_id"]),
                    uploaded_file,
                    category=request.POST.get("document_category", "OTHER") or "OTHER",
                    uploaded_by=user["id"],
                    notes=request.POST.get("document_notes") or None,
                )

                AuditService().create(
                    user_id=user["id"],
                    action="DOCUMENT_UPLOADED",
                    entity_type="customer",
                    entity_id=str(customer["_id"]),
                    description=f"Document '{uploaded_file.name}' was uploaded.",
                )

        except ValueError as exc:
            # Keep the submitted values when validation fails
            record = {
                "id": id,
                "customer_number": customer.get("customer_number"),
                "first_name": request.POST.get("first_name", ""),
                "last_name": request.POST.get("last_name", ""),
                "status": request.POST.get("status", "ACTIVE"),
                "email": request.POST.get("email", ""),
                "phone": request.POST.get("phone", ""),
                "phone_full": request.POST.get("phone_full", ""),
                "date_of_birth": request.POST.get("date_of_birth", ""),
                "nationality": request.POST.get("nationality", ""),

                "address": {
                    "country": request.POST.get("address_country", ""),
                    "city": request.POST.get("address_city", ""),
                    "street": request.POST.get("address_street", ""),
                },

                "passport": {
                    "number": request.POST.get("passport_number", ""),
                    "expiry_date": request.POST.get(
                        "passport_expiry_date",
                        "",
                    ),
                    "issuing_country": request.POST.get(
                        "passport_issuing_country",
                        "",
                    ),
                },

                "emergency_contact": {
                    "name": request.POST.get(
                        "emergency_contact_name",
                        "",
                    ),
                    "phone": request.POST.get(
                        "emergency_contact_phone",
                        "",
                    ),
                    "phone_full": request.POST.get(
                        "emergency_contact_phone_full",
                        "",
                    ),
                    "relationship": request.POST.get(
                        "emergency_contact_relationship",
                        "",
                    ),
                },

                "notes": request.POST.get("notes", ""),
            }

            first = record["first_name"]
            last = record["last_name"]

            return wireframe(
                request,
                "customers/form.html",
                "Edit customer",
                heading=f"Edit {first} {last}".strip(),
                error=str(exc),
                record=record,
                edit_mode=True,
            )

        return redirect(
            "customers:detail",
            id=str(customer["_id"]),
        )

    # GET — populate the form from MongoDB
    first = customer.get("first_name", "")
    last = customer.get("last_name", "")

    row = {
        "id": str(customer["_id"]),
        "customer_number": customer.get("customer_number", ""),
        "first_name": first,
        "last_name": last,
        "name": f"{first} {last}".strip(),
        "status": customer.get("status", "ACTIVE"),
        "email": customer.get("email", ""),
        "phone": customer.get("phone", ""),
        "phone_full": customer.get("phone", ""),
        "date_of_birth": customer.get("date_of_birth", ""),
        "nationality": customer.get("nationality", ""),

        "address": {
            "country": customer.get("address", {}).get("country", ""),
            "city": customer.get("address", {}).get("city", ""),
            "street": customer.get("address", {}).get("street", ""),
        },

        "passport": {
            "number": customer.get("passport", {}).get("number", ""),
            "expiry_date": customer.get("passport", {}).get(
                "expiry_date",
                "",
            ),
            "issuing_country": customer.get("passport", {}).get(
                "issuing_country",
                "",
            ),
        },

        "emergency_contact": {
            "name": customer.get("emergency_contact", {}).get(
                "name",
                "",
            ),
            "phone": customer.get("emergency_contact", {}).get(
                "phone",
                "",
            ),
            "phone_full": customer.get("emergency_contact", {}).get(
                "phone",
                "",
            ),
            "relationship": customer.get("emergency_contact", {}).get(
                "relationship",
                "",
            ),
        },

        "notes": customer.get("notes", ""),
    }

    return wireframe(
        request,
        "customers/form.html",
        "Edit customer",
        heading=f"Edit {row['name']}",
        record=row,
        edit_mode=True,
    )


@login_required
@role_required(UserRole.TRAVEL_AGENT, UserRole.OWNER_ADMIN)
def customer_attachment_delete(request, id, attachment_id):
    if request.method == "POST":
        user = get_session_user(request)

        AttachmentService().delete(
            attachment_id,
            user["id"],
        )

        AuditService().create(
            user_id=user["id"],
            action="DOCUMENT_DELETED",
            entity_type="customer",
            entity_id=id,
            description="A customer document was deleted.",
        )

    return redirect(
        f"/customers/{id}/?tab=documents"
    )