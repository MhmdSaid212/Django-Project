from apps.audit.repositories import AuditLogRepository


class AuditService:
    def __init__(self, repository: AuditLogRepository | None = None):
        self.repository = repository or AuditLogRepository()

    def list_items(self):
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
