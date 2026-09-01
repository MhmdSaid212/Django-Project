from core.responses import not_implemented

def list_supplier_payments(request, **kwargs):
    return not_implemented("GET /api/supplier-payments/ is not implemented yet. Owner: Dev 4.")

def create_supplier_payment(request, **kwargs):
    return not_implemented("POST /api/supplier-payments/ is not implemented yet. Owner: Dev 4.")

def supplier_payments_for_supplier(request, **kwargs):
    return not_implemented("GET /api/suppliers/<supplier_id>/payments/ is not implemented yet. Owner: Dev 4.")

def create_supplier_payment_for_supplier(request, **kwargs):
    return not_implemented("POST /api/suppliers/<supplier_id>/payments/ is not implemented yet. Owner: Dev 4.")
