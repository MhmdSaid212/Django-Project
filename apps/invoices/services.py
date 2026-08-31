"""
Business rules.

OWNER: Dev 3 — Customer Finance

taxable_amount = subtotal - discount; total = taxable_amount + tax.
"""
from apps.invoices.repositories import InvoiceRepository


class InvoiceService:
    def __init__(self, repository: InvoiceRepository | None = None):
        self.repository = repository or InvoiceRepository()

    def list_items(self):
        # TODO: replace with real list + pagination.
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
