"""JSON API placeholders.

OWNER: Shared — all developers
"""
from core.responses import not_implemented

def list_notifications(request, **kwargs):
    return not_implemented("GET /api/notifications/ is not implemented yet.")
