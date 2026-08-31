"""
Business rules.

OWNER: Dev 3 — Customer Finance

Usually created when a payment is recorded.
"""
from apps.receipts.repositories import ReceiptRepository


class ReceiptService:
    def __init__(self, repository: ReceiptRepository | None = None):
        self.repository = repository or ReceiptRepository()

    def list_items(self):
        # TODO: replace with real list + pagination.
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
