"""JSON API placeholders.

OWNER: Dev 3 — Customer Finance
"""
from core.responses import not_implemented

def list_payments(request, **kwargs):
    return not_implemented("GET /api/payments/ is not implemented yet. Owner: Dev 3.")

def create_payment(request, **kwargs):
    return not_implemented("POST /api/payments/ is not implemented yet. Owner: Dev 3.")

def get_payment(request, **kwargs):
    return not_implemented("GET /api/payments/<id>/ is not implemented yet. Owner: Dev 3.")

def payments_for_invoice(request, **kwargs):
    return not_implemented("GET /api/invoices/<invoice_id>/payments/ is not implemented yet. Owner: Dev 3.")

def create_payment_for_invoice(request, **kwargs):
    return not_implemented("POST /api/invoices/<invoice_id>/payments/ is not implemented yet. Owner: Dev 3.")
