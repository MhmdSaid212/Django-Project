from __future__ import annotations

from pymongo.collection import Collection

from core.database import get_collection
from core.soft_delete import SoftDeleteRepositoryMixin, live_query


class AttachmentRepository(SoftDeleteRepositoryMixin):
    def __init__(self, collection: Collection | None = None):
        self.collection = collection or get_collection("attachments")

    def list_for_entity(
        self,
        entity_type: str,
        entity_id,
        *,
        limit: int = 100,
    ) -> list[dict]:
        query = live_query({
            "entity_type": entity_type,
            "entity_id": entity_id,
        })

        return list(
            self.collection
            .find(query)
            .sort("created_at", -1)
            .limit(limit)
        )

    def insert_attachment(self, document: dict):
        result = self.collection.insert_one(document)
        document["_id"] = result.inserted_id
        return document