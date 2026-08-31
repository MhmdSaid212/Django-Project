"""JSON API placeholders.

OWNER: Dev 2 — Travel Products & Suppliers
"""
from core.responses import not_implemented

def list_packages(request, **kwargs):
    return not_implemented("GET /api/packages/ is not implemented yet. Owner: Dev 2.")

def create_package(request, **kwargs):
    return not_implemented("POST /api/packages/ is not implemented yet. Owner: Dev 2.")

def get_package(request, **kwargs):
    return not_implemented("GET /api/packages/<id>/ is not implemented yet. Owner: Dev 2.")

def patch_package(request, **kwargs):
    return not_implemented("PATCH /api/packages/<id>/ is not implemented yet. Owner: Dev 2.")
