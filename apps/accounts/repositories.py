"""
MongoDB access for users. No Django ORM.

Deleted users cannot log in. Use soft_delete — never delete_one().
INACTIVE status is different: the account exists and can be reactivated.
"""
from __future__ import annotations

from bson import ObjectId
from pymongo.collection import Collection

from core.constants import Collections, UserStatus
from core.database import get_collection
from core.soft_delete import LIVE_FILTER, SoftDeleteRepositoryMixin, live_query, stamp_new
from core.utils import parse_object_id


class UserRepository(SoftDeleteRepositoryMixin):
    def __init__(self, collection: Collection | None = None):
        self.collection = collection or get_collection(Collections.USERS)

    def find_by_email(self, email: str, *, include_deleted: bool = False) -> dict | None:
        query = {"email": email.strip().lower()}
        if not include_deleted:
            query.update(LIVE_FILTER)
        return self.collection.find_one(query)

    def find_by_id(self, user_id: str | ObjectId, *, include_deleted: bool = False) -> dict | None:
        query = {"_id": parse_object_id(user_id, field="user_id")}
        if not include_deleted:
            query.update(LIVE_FILTER)
        return self.collection.find_one(query)

    def insert(self, document: dict):
        return self.collection.insert_one(stamp_new(document))

    def update_last_login(self, user_id, when) -> None:
        self.collection.update_one(live_query({"_id": user_id}), {"$set": {"last_login_at": when}})

    def list_active(self) -> list[dict]:
        return list(
            self.collection.find(live_query({"status": UserStatus.ACTIVE.value}))
        )
