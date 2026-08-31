"""
Business rules.

OWNER: Dev 4 — Business Finance & Reports

Actual money paid to a supplier against an expense.
"""
from apps.supplier_payments.repositories import SupplierPaymentRepository


class SupplierPaymentService:
    def __init__(self, repository: SupplierPaymentRepository | None = None):
        self.repository = repository or SupplierPaymentRepository()

    def list_items(self):
        # TODO: replace with real list + pagination.
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
