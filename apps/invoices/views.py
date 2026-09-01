"""
HTML views for invoices.  OWNER: Dev 3 — Customer Finance
Server-side rendered: each view calls InvoiceService and hands the template
a plain dict shaped for display. No JSON/JS round-trip.

TEMP MOCK MODE
--------------
USE_MOCK_DATA below swaps InvoiceService for hardcoded dicts, and auth
decorators are commented out, so these pages work with ZERO database
connection and ZERO login. This is for local visual review only.

To restore the real, database-backed, login-protected behavior:
  1. Set USE_MOCK_DATA = False
  2. Uncomment the three "# @login_required" / "# @role_required(...)" lines
That's it -- every other line of this file is the real implementation either way.
"""
from datetime import datetime, timezone

from django.shortcuts import render

from apps.invoices.repositories import InvoiceRepository
from apps.invoices.services import InvoiceService, present_invoice
from core.constants import InvoiceStatus, UserRole
from core.permissions import login_required, role_required

# --- TEMP: flip to False (and uncomment the decorators below) once MongoDB
# is connected and you're ready to test against real data. ---
USE_MOCK_DATA = True

# Status filter tabs shown on the list page (value, label).
STATUS_TABS = [
    ("", "All Statuses"),
    (InvoiceStatus.DRAFT.value, "Draft"),
    (InvoiceStatus.ISSUED.value, "Issued"),
    (InvoiceStatus.PARTIALLY_PAID.value, "Partially Paid"),
    (InvoiceStatus.PAID.value, "Paid"),
    (InvoiceStatus.CANCELLED.value, "Cancelled"),
]

# --- TEMP mock data (same shape present_invoice()/_get_raw() would return) ---
_MOCK_ROWS = [
    {"id": "1", "number": "INV-2088", "customer": "Sarah Ahmad", "booking": "BK-1042",
     "issue": "May 18, 2025", "due": "Jun 01, 2025", "total": 2090, "paid": 500,
     "remaining": 1590, "status": "PARTIALLY_PAID", "overdue": False},
    {"id": "2", "number": "INV-2081", "customer": "Michael Thompson", "booking": "BK-1035",
     "issue": "Apr 28, 2025", "due": "May 12, 2025", "total": 4500, "paid": 4500,
     "remaining": 0, "status": "PAID", "overdue": False},
    {"id": "3", "number": "INV-2085", "customer": "Daniel Carter", "booking": "BK-1039",
     "issue": "May 10, 2025", "due": "May 20, 2025", "total": 1100, "paid": 0,
     "remaining": 1100, "status": "ISSUED", "overdue": True},
]

_MOCK_RECORDS = {
    "1": {
        "id": "1", "number": "INV-2088", "status": "PARTIALLY_PAID",
        "customer": "Sarah Ahmad", "customer_email": "sarah.ahmad@example.com",
        "booking": "BK-1042", "issue": "May 18, 2025", "due": "Jun 01, 2025",
        "items": [{"description": "Istanbul Tour -- 2 travelers", "quantity": 2,
                    "unit_price": 1000, "total": 2000}],
        "subtotal": 2000, "discount_amount": 100, "tax_rate": "9.5", "tax_amount": 190,
        "total": 2090, "paid": 500, "remaining": 1590, "overdue": False,
    },
    "2": {
        "id": "2", "number": "INV-2081", "status": "PAID",
        "customer": "Michael Thompson", "customer_email": "michael.t@example.com",
        "booking": "BK-1035", "issue": "Apr 28, 2025", "due": "May 12, 2025",
        "items": [{"description": "Dubai Desert Safari -- 4 travelers", "quantity": 4,
                    "unit_price": 1125, "total": 4500}],
        "subtotal": 4500, "discount_amount": 0, "tax_rate": "0", "tax_amount": 0,
        "total": 4500, "paid": 4500, "remaining": 0, "overdue": False,
    },
}


def _fmt_date(value):
    if not value:
        return "--"
    if isinstance(value, datetime):
        return value.strftime("%b %d, %Y")
    return str(value)


def _is_overdue(inv: dict) -> bool:
    """Overdue is DERIVED, not stored: issued/partly-paid and past the due date."""
    if inv.get("status") not in (InvoiceStatus.ISSUED.value, InvoiceStatus.PARTIALLY_PAID.value):
        return False
    due = inv.get("due_date")
    if not isinstance(due, datetime):
        return False
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    return due < datetime.now(timezone.utc)


def _row(inv: dict) -> dict:
    """Shape one presented invoice for the list table."""
    return {
        "id": inv["id"],
        "number": inv["invoice_number"],
        "customer": inv.get("customer_name") or "--",
        "booking": inv.get("booking_number") or "--",
        "issue": _fmt_date(inv.get("issue_date")),
        "due": _fmt_date(inv.get("due_date")),
        "total": inv.get("total_amount"),
        "paid": inv.get("paid_amount"),
        "remaining": inv.get("remaining_amount"),
        "status": inv.get("status"),
        "overdue": _is_overdue(inv),
    }


# TEMP: auth disabled for local preview -- restore before merging
# @login_required
# @role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def invoice_list(request):
    status = request.GET.get("status") or None
    search = (request.GET.get("q") or "").strip().lower()

    if USE_MOCK_DATA:
        all_rows = list(_MOCK_ROWS)
        rows = all_rows
        if status:
            rows = [r for r in rows if r["status"] == status]
    else:
        service = InvoiceService()
        invoices = service.list_items(status=status)
        rows = [_row(i) for i in invoices]
        all_rows = [_row(i) for i in service.list_items()]

    if search:
        rows = [
            r for r in rows
            if search in str(r["number"]).lower()
            or search in str(r["customer"]).lower()
            or search in str(r["booking"]).lower()
        ]

    counts = {value: 0 for value, _ in STATUS_TABS}
    counts[""] = len(all_rows)
    for r in all_rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    context = {
        "page_title": "Invoices",
        "page_heading": "Invoices",
        "rows": rows,
        "status_tabs": [
            {"value": v, "label": l, "count": counts.get(v, 0), "active": (status or "") == v}
            for v, l in STATUS_TABS
        ],
        "search": request.GET.get("q", ""),
        "total_count": len(all_rows),
    }
    return render(request, "invoices/list.html", context)


# TEMP: auth disabled for local preview -- restore before merging
# @login_required
# @role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def invoice_detail(request, id):
    if USE_MOCK_DATA:
        record = dict(_MOCK_RECORDS.get(id, _MOCK_RECORDS["1"]))
    else:
        service = InvoiceService()
        raw = service._get_raw(id)          # raises NotFoundError -> handled by core error views
        inv = present_invoice(raw)
        items = [{
            "description": li.get("description", ""),
            "quantity": li.get("quantity", 1),
            "unit_price": li.get("unit_price", 0),
            "total": li.get("total", 0),
        } for li in raw.get("line_items", [])]
        discount = raw.get("discount", {}) or {}
        tax = raw.get("tax", {}) or {}
        record = {
            "id": inv["id"],
            "number": inv["invoice_number"],
            "status": inv["status"],
            "customer": inv.get("customer_name") or "--",
            "customer_email": inv.get("customer_email") or "",
            "booking": inv.get("booking_number") or "--",
            "issue": _fmt_date(raw.get("issue_date")),
            "due": _fmt_date(raw.get("due_date")),
            "items": items,
            "subtotal": inv.get("subtotal"),
            "discount_amount": discount.get("amount", 0),
            "tax_rate": tax.get("rate", 0),
            "tax_amount": tax.get("amount", 0),
            "total": inv.get("total_amount"),
            "paid": inv.get("paid_amount"),
            "remaining": inv.get("remaining_amount"),
            "overdue": _is_overdue(raw),
        }

    context = {
        "page_title": record["number"],
        "page_heading": record["number"],
        "crumbs": [
            {"label": "Invoices", "url": "/invoices/"},
            {"label": record["number"], "url": ""},
        ],
        "record": record,
    }
    return render(request, "invoices/detail.html", context)


# TEMP: auth disabled for local preview -- restore before merging
# @login_required
# @role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def invoice_print(request, id):
    """Print view reuses the detail data, stripped-down template."""
    if USE_MOCK_DATA:
        record = dict(_MOCK_RECORDS.get(id, _MOCK_RECORDS["1"]))
    else:
        service = InvoiceService()
        raw = service._get_raw(id)
        inv = present_invoice(raw)
        record = {**inv, "number": inv["invoice_number"]}

    context = {
        "page_title": "Print " + record["number"],
        "page_heading": record["number"],
        "record": record,
    }
    return render(request, "invoices/print.html", context)

# --- TEMP mock: confirmed bookings awaiting an invoice (no DB) ---
_MOCK_BOOKINGS = [
    {"id": "b1", "number": "BK-1042", "customer": "Sarah Ahmad", "avatar": "#f59e0b",
     "tour": "Istanbul Tour", "travelers": 2, "amount": 2090},
    {"id": "b2", "number": "BK-1043", "customer": "Raj Kumar", "avatar": "#6366f1",
     "tour": "Dubai Safari", "travelers": 4, "amount": 4500},
    {"id": "b3", "number": "BK-1044", "customer": "Emily Harris", "avatar": "#0f766e",
     "tour": "Cairo Pyramids", "travelers": 2, "amount": 1980},
]


# TEMP: auth disabled for local preview -- restore before merging
# @login_required
# @role_required(UserRole.ACCOUNTANT, UserRole.OWNER_ADMIN)
def invoice_create(request):
    if USE_MOCK_DATA:
        bookings = _MOCK_BOOKINGS
    else:
        # Real mode: query CONFIRMED bookings that don't yet have a live invoice.
        # (Dev 1 owns bookings; when connected, replace with the real query.)
        bookings = []
    context = {
        "page_title": "Create Invoice",
        "page_heading": "Create Invoice",
        "bookings": bookings,
    }
    return render(request, "invoices/create.html", context)