"""
Business rules.

OWNER: Shared — Owner/Admin UI, all developers write logs

Never log passwords or secrets. Write an audit record from services after mutations.
"""
from apps.audit.repositories import AuditLogRepository


class AuditService:
    def __init__(self, repository: AuditLogRepository | None = None):
        self.repository = repository or AuditLogRepository()

    def list_items(self):
        # TODO: replace with real list + pagination.
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
