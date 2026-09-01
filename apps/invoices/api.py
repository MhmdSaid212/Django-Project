from core.responses import not_implemented

def list_invoices(request, **kwargs):
    return not_implemented("GET /api/invoices/ is not implemented yet. Owner: Dev 3.")

def create_invoice(request, **kwargs):
    return not_implemented("POST /api/invoices/ is not implemented yet. Owner: Dev 3.")

def get_invoice(request, **kwargs):
    return not_implemented("GET /api/invoices/<id>/ is not implemented yet. Owner: Dev 3.")

def patch_invoice(request, **kwargs):
    return not_implemented("PATCH /api/invoices/<id>/ is not implemented yet. Owner: Dev 3.")

def create_invoice_for_booking(request, **kwargs):
    return not_implemented("POST /api/bookings/<booking_id>/invoice/ is not implemented yet. Owner: Dev 3.")
