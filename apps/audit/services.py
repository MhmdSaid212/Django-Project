from apps.audit.repositories import AuditLogRepository
from core.utils import parse_object_id, utcnow


class AuditService:
    def __init__(self, repository: AuditLogRepository | None = None):
        self.repository = repository or AuditLogRepository()

    def list_items(self):
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)

    def create(
        self,
        *,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        description: str,
        before=None,
        after=None,
        ip_address=None,
    ):
        document = {
            "user_id": parse_object_id(user_id, field="user_id"),
            "action": action,
            "entity_type": entity_type,
            "entity_id": parse_object_id(entity_id, field="entity_id"),
            "description": description,
            "created_at": utcnow(),
            "before": before,
            "after": after,
            "ip_address": ip_address,
        }

        return self.repository.insert(document)