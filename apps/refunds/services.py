"""
Business rules.

OWNER: Dev 3 — Customer Finance

Never delete a payment to represent a refund.
"""
from apps.refunds.repositories import RefundRepository


class RefundService:
    def __init__(self, repository: RefundRepository | None = None):
        self.repository = repository or RefundRepository()

    def list_items(self):
        # TODO: replace with real list + pagination.
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
