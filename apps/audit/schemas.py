"""
Audit log document contract. NOT a Django model.

OWNER: Shared — Owner/Admin UI, all developers write logs.
Collection: audit_logs

Never log passwords, password hashes, or secrets.
Audit logs are append-only: do not update, hard-delete, or soft-delete them.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from bson import ObjectId


@dataclass
class AuditLogDocument:
    user_id: ObjectId
    action: str
    entity_type: str
    entity_id: ObjectId
    description: str
    created_at: datetime
    before: Optional[dict[str, Any]] = None
    after: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    _id: Optional[ObjectId] = None
