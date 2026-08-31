"""JSON API placeholders.

OWNER: Dev 1 — Customer & Booking Operations
"""
from core.responses import not_implemented

def list_customers(request, **kwargs):
    return not_implemented("GET /api/customers/ is not implemented yet. Owner: Dev 1.")

def create_customer(request, **kwargs):
    return not_implemented("POST /api/customers/ is not implemented yet. Owner: Dev 1.")

def get_customer(request, **kwargs):
    return not_implemented("GET /api/customers/<id>/ is not implemented yet. Owner: Dev 1.")

def patch_customer(request, **kwargs):
    return not_implemented("PATCH /api/customers/<id>/ is not implemented yet. Owner: Dev 1.")
