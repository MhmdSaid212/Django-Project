from pymongo.collection import Collection

from core.constants import Collections
from core.database import get_collection
from core.utils import parse_object_id


class AuditLogRepository:
    def __init__(self, collection: Collection | None = None):
        self.collection = collection or get_collection(Collections.AUDIT_LOGS)

    def find_all(self, limit: int = 50) -> list[dict]:
        return list(self.collection.find({}).sort("created_at", -1).limit(limit))

    def find_by_id(self, doc_id: str) -> dict | None:
        return self.collection.find_one({"_id": parse_object_id(doc_id)})

    def insert(self, document: dict):
        return self.collection.insert_one(document)
