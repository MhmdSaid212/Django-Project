"""JSON API placeholders.

OWNER: Dev 2 — Travel Products & Suppliers
"""
from core.responses import not_implemented

def list_tours(request, **kwargs):
    return not_implemented("GET /api/tours/ is not implemented yet. Owner: Dev 2.")

def create_tour(request, **kwargs):
    return not_implemented("POST /api/tours/ is not implemented yet. Owner: Dev 2.")

def get_tour(request, **kwargs):
    return not_implemented("GET /api/tours/<id>/ is not implemented yet. Owner: Dev 2.")

def patch_tour(request, **kwargs):
    return not_implemented("PATCH /api/tours/<id>/ is not implemented yet. Owner: Dev 2.")

def tour_availability(request, **kwargs):
    return not_implemented("GET /api/tours/<id>/availability/ is not implemented yet. Owner: Dev 2 / Dev 1.")
