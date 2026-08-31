"""
Soft delete — shared contract for all four developers.

Decision:
    Business documents are never removed with delete_one / delete_many.
    A "delete" in the UI sets:

        is_deleted = True
        deleted_at = utcnow()
        deleted_by = current user ObjectId

    Default list/get queries MUST hide those rows.

This is different from status ACTIVE / INACTIVE:
    INACTIVE  = still in the system, but not usable for new bookings (etc.)
    is_deleted = hidden from normal screens, kept for history and audits

Never reuse this for refunds. A refund is a new refund document.
Never hard-delete a payment, invoice, or booking to "undo" it.

Not soft-deleted (append-only or singleton):
    audit_logs, system_settings, counters
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from bson import ObjectId

from core.utils import parse_object_id, utcnow

# Use $ne True so older documents that omitted the field still count as live.
LIVE_FILTER = {"is_deleted": {"$ne": True}}


def live_query(extra: dict | None = None) -> dict:
    """MongoDB filter for rows that are not soft-deleted."""
    query = dict(LIVE_FILTER)
    if extra:
        query.update(extra)
    return query


def stamp_new(document: dict) -> dict:
    """Every insert should set the live flag explicitly."""
    stamped = dict(document)
    stamped.setdefault("is_deleted", False)
    stamped.setdefault("deleted_at", None)
    stamped.setdefault("deleted_by", None)
    return stamped


def deletion_set(deleted_by: str | ObjectId) -> dict:
    now = utcnow()
    user_id = deleted_by if isinstance(deleted_by, ObjectId) else parse_object_id(deleted_by, field="deleted_by")
    return {
        "is_deleted": True,
        "deleted_at": now,
        "deleted_by": user_id,
        "updated_at": now,
    }


def restore_set() -> dict:
    return {
        "is_deleted": False,
        "deleted_at": None,
        "deleted_by": None,
        "updated_at": utcnow(),
    }


class SoftDeleteRepositoryMixin:
    """
    Live-document filtering for a feature repository.

    This is not a generic CRUD base class. Each app still owns its repository
    so developers can add feature-specific queries next to these helpers.
    """

    collection = None  # set in the feature repository __init__

    def find_all(self, limit: int = 50, *, include_deleted: bool = False) -> list[dict]:
        query = {} if include_deleted else live_query()
        return list(self.collection.find(query).limit(limit))

    def find_by_id(self, doc_id: str, *, include_deleted: bool = False) -> dict | None:
        query = {"_id": parse_object_id(doc_id)}
        if not include_deleted:
            query.update(LIVE_FILTER)
        return self.collection.find_one(query)

    def insert(self, document: dict):
        return self.collection.insert_one(stamp_new(document))

    def update(self, doc_id: str, updates: dict):
        """Update a live document only. Do not pass is_deleted here — use soft_delete()."""
        clean = {key: value for key, value in updates.items() if key not in {"is_deleted", "deleted_at", "deleted_by"}}
        return self.collection.update_one(
            live_query({"_id": parse_object_id(doc_id)}),
            {"$set": clean},
        )

    def soft_delete(self, doc_id: str, deleted_by: str | ObjectId):
        return self.collection.update_one(
            live_query({"_id": parse_object_id(doc_id)}),
            {"$set": deletion_set(deleted_by)},
        )

    def restore(self, doc_id: str):
        """Owner/admin restore. Include deleted rows when looking the id up."""
        return self.collection.update_one(
            {"_id": parse_object_id(doc_id), "is_deleted": True},
            {"$set": restore_set()},
        )
