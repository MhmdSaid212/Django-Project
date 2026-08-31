"""JSON API placeholders.

OWNER: Dev 4 — Business Finance & Reports
"""
from core.responses import not_implemented

def customer_balance(request, **kwargs):
    return not_implemented("GET /api/customers/<customer_id>/balance/ is not implemented yet. Owner: Dev 4.")

def supplier_balance(request, **kwargs):
    return not_implemented("GET /api/suppliers/<supplier_id>/balance/ is not implemented yet. Owner: Dev 4.")

def receivables(request, **kwargs):
    return not_implemented("GET /api/finance/receivables/ is not implemented yet. Owner: Dev 4.")

def payables(request, **kwargs):
    return not_implemented("GET /api/finance/payables/ is not implemented yet. Owner: Dev 4.")

def tour_profitability(request, **kwargs):
    return not_implemented("GET /api/tours/<tour_id>/profitability/ is not implemented yet. Owner: Dev 4.")
