"""
Business rules.

OWNER: Dev 4 — Business Finance & Reports

Expense is the cost incurred. Supplier payments are separate.
"""
from apps.expenses.repositories import ExpenseRepository


class ExpenseService:
    def __init__(self, repository: ExpenseRepository | None = None):
        self.repository = repository or ExpenseRepository()

    def list_items(self):
        # TODO: replace with real list + pagination.
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
