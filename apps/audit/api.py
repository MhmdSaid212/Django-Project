"""JSON API placeholders.

OWNER: Shared — Owner/Admin UI, all developers write logs
"""
from core.responses import not_implemented

def list_audit_logs(request, **kwargs):
    return not_implemented("GET /api/audit/ is not implemented yet.")
