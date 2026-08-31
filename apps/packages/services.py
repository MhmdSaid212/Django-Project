"""
Business rules.

OWNER: Dev 2 — Travel Products & Suppliers

Packages are product templates. Clients never book a package directly.
Create a tour from a package (copy price/services, set dates + capacity),
then bookings attach to that tour.
"""
from apps.packages.repositories import PackageRepository


class PackageService:
    def __init__(self, repository: PackageRepository | None = None):
        self.repository = repository or PackageRepository()

    def list_items(self):
        # TODO: replace with real list + pagination.
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
