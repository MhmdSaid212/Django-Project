"""
Business rules.

OWNER: Dev 3 — Customer Finance

Update invoice paid_amount and status. Never delete a payment to refund.
"""
from apps.payments.repositories import PaymentRepository


class PaymentService:
    def __init__(self, repository: PaymentRepository | None = None):
        self.repository = repository or PaymentRepository()

    def list_items(self):
        # TODO: replace with real list + pagination.
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
