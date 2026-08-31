"""JSON API placeholders.

OWNER: Dev 1 — Customer & Booking Operations
"""
from core.responses import not_implemented

def list_bookings(request, **kwargs):
    return not_implemented("GET /api/bookings/ is not implemented yet. Owner: Dev 1.")

def create_booking(request, **kwargs):
    return not_implemented("POST /api/bookings/ is not implemented yet. Owner: Dev 1.")

def get_booking(request, **kwargs):
    return not_implemented("GET /api/bookings/<id>/ is not implemented yet. Owner: Dev 1.")

def patch_booking(request, **kwargs):
    return not_implemented("PATCH /api/bookings/<id>/ is not implemented yet. Owner: Dev 1.")

def confirm_booking(request, **kwargs):
    return not_implemented("POST /api/bookings/<id>/confirm/ is not implemented yet. Owner: Dev 1.")

def cancel_booking(request, **kwargs):
    return not_implemented("POST /api/bookings/<id>/cancel/ is not implemented yet. Owner: Dev 1.")
