"""
Business rules.

OWNER: Dev 2 — Travel Products & Suppliers

Hotels / transportation / tour guides stay in this collection.
Fill only the embed that matches supplier_type (hotel_info, transportation_info, …).
"""
from apps.suppliers.repositories import SupplierRepository


class SupplierService:
    def __init__(self, repository: SupplierRepository | None = None):
        self.repository = repository or SupplierRepository()

    def list_items(self):
        # TODO: replace with real list + pagination.
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
