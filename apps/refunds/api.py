"""JSON API placeholders.

OWNER: Dev 3 — Customer Finance
"""
from core.responses import not_implemented

def list_refunds(request, **kwargs):
    return not_implemented("GET /api/refunds/ is not implemented yet. Owner: Dev 3.")

def create_refund(request, **kwargs):
    return not_implemented("POST /api/refunds/ is not implemented yet. Owner: Dev 3.")

def get_refund(request, **kwargs):
    return not_implemented("GET /api/refunds/<id>/ is not implemented yet. Owner: Dev 3.")

def refund_from_payment(request, **kwargs):
    return not_implemented("POST /api/payments/<payment_id>/refund/ is not implemented yet. Owner: Dev 3.")
