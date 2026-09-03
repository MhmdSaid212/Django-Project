"""
PREVIEW ONLY — zero database calls. Renders the REAL invoice templates with
hand-built mock data so you can look at the pages before MongoDB is connected.

Not linked from any nav menu. Visit directly:
    /invoices/preview/
    /invoices/preview/1/      (PARTIALLY_PAID example, matches the mockups)
    /invoices/preview/2/      (PAID example)

DELETE THIS FILE (and its two url lines) once you're done previewing —
it is not part of the real Dev 3 deliverable, just a visual sanity check.
"""
from django.shortcuts import render

from core.permissions import SESSION_USER_KEY

_FAKE_USER = {
    "id": "000000000000000000000001",
    "email": "accountant@tourops.local",
    "first_name": "Karim",
    "last_name": "Books",
    "role": "ACCOUNTANT",
}

_MOCK_INVOICES = {
    "1": {
        "id": "1",
        "invoice_number": "INV-2088",
        "booking": "BK-1042",
        "customer": "Sarah Ahmad",
        "customer_email": "sarah.ahmad@example.com",
        "issue": "May 18, 2025",
        "due": "Jun 01, 2025",
        "items": [
            {"description": "Istanbul Tour — 2 travelers", "quantity": 2, "unit_price": 1000, "total": 2000},
        ],
        "subtotal": 2000,
        "discount_amount": 100,
        "tax_rate": "9.5",
        "tax_amount": 190,
        "total": 2090,
        "paid": 500,
        "remaining": 1590,
        "status": "PARTIALLY_PAID",
        "overdue": False,
    },
    "2": {
        "id": "2",
        "invoice_number": "INV-2081",
        "booking": "BK-1035",
        "customer": "Michael Thompson",
        "customer_email": "michael.t@example.com",
        "issue": "Apr 28, 2025",
        "due": "May 12, 2025",
        "items": [
            {"description": "Dubai Desert Safari — 4 travelers", "quantity": 4, "unit_price": 1125, "total": 4500},
        ],
        "subtotal": 4500,
        "discount_amount": 0,
        "tax_rate": "0",
        "tax_amount": 0,
        "total": 4500,
        "paid": 4500,
        "remaining": 0,
        "status": "PAID",
        "overdue": False,
    },
}

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


def _fake_session(request):
    """Plant a session user without touching the DB, so base.html renders fully."""
    request.session[SESSION_USER_KEY] = _FAKE_USER


def preview_invoice_list(request):
    _fake_session(request)
    context = {
        "page_title": "Invoices (Preview)",
        "page_heading": "Invoices",
        "rows": _MOCK_ROWS,
        "status_tabs": [
            {"value": "", "label": "All Statuses", "count": len(_MOCK_ROWS), "active": True},
            {"value": "ISSUED", "label": "Issued", "count": 1, "active": False},
            {"value": "PARTIALLY_PAID", "label": "Partially Paid", "count": 1, "active": False},
            {"value": "PAID", "label": "Paid", "count": 1, "active": False},
        ],
        "search": "",
        "total_count": len(_MOCK_ROWS),
    }
    return render(request, "invoices/list.html", context)


def preview_invoice_detail(request, id="1"):
    _fake_session(request)
    record = _MOCK_INVOICES.get(id, _MOCK_INVOICES["1"])
    context = {
        "page_title": record["invoice_number"],
        "page_heading": record["invoice_number"],
        "crumbs": [{"label": "Invoices", "url": "/invoices/preview/"}, {"label": record["invoice_number"], "url": ""}],
        "record": {**record, "number": record["invoice_number"]},
    }
    return render(request, "invoices/detail.html", context)
