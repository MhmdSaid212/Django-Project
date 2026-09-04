from __future__ import annotations

from django.core.files.storage import default_storage

from apps.attachments.repositories import AttachmentRepository
from core.utils import parse_object_id, serialize_id, utcnow


class AttachmentService:
    def __init__(self, repository=None):
        self.repository = repository or AttachmentRepository()

    def list_for_customer(self, customer_id: str) -> list[dict]:
        attachments = self.repository.list_for_entity(
            "customer",
            parse_object_id(customer_id, field="customer_id"),
        )

        return [
            {
                "id": serialize_id(doc.get("_id")),
                "file_name": doc.get("file_name", ""),
                "category": doc.get("category", ""),
                "content_type": doc.get("content_type", ""),
                "storage_key": doc.get("storage_key", ""),
                "notes": doc.get("notes"),
                "created_at": doc.get("created_at"),
                "uploaded_by": serialize_id(doc.get("uploaded_by")),
            }
            for doc in attachments
        ]

    def upload_for_customer(
        self,
        customer_id: str,
        uploaded_file,
        *,
        category: str,
        uploaded_by: str,
        notes: str | None = None,
    ) -> dict:

        customer_object_id = parse_object_id(
            customer_id,
            field="customer_id",
        )

        uploaded_by_object_id = parse_object_id(
            uploaded_by,
            field="uploaded_by",
        )

        storage_key = default_storage.save(
            f"customer_documents/{customer_id}/{uploaded_file.name}",
            uploaded_file,
        )

        document = {
            "entity_type": "customer",
            "entity_id": customer_object_id,
            "category": category,
            "file_name": uploaded_file.name,
            "content_type": uploaded_file.content_type or "",
            "storage_key": storage_key,
            "uploaded_by": uploaded_by_object_id,
            "created_at": utcnow(),
            "notes": notes,
            "is_deleted": False,
            "deleted_at": None,
            "deleted_by": None,
        }

        return self.repository.insert_attachment(document)

    def delete(self, attachment_id: str, deleted_by: str):
        return self.repository.soft_delete(
            attachment_id,
            deleted_by=parse_object_id(deleted_by, field="deleted_by"),
        )