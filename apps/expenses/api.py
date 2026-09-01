from core.responses import not_implemented

def list_expenses(request, **kwargs):
    return not_implemented("GET /api/expenses/ is not implemented yet. Owner: Dev 4.")

def create_expense(request, **kwargs):
    return not_implemented("POST /api/expenses/ is not implemented yet. Owner: Dev 4.")

def get_expense(request, **kwargs):
    return not_implemented("GET /api/expenses/<id>/ is not implemented yet. Owner: Dev 4.")

def patch_expense(request, **kwargs):
    return not_implemented("PATCH /api/expenses/<id>/ is not implemented yet. Owner: Dev 4.")

def expenses_for_tour(request, **kwargs):
    return not_implemented("GET /api/tours/<tour_id>/expenses/ is not implemented yet. Owner: Dev 4.")

def expenses_for_supplier(request, **kwargs):
    return not_implemented("GET /api/suppliers/<supplier_id>/expenses/ is not implemented yet. Owner: Dev 4.")
