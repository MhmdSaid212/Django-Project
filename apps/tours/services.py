"""
Business rules.

OWNER: Dev 2 — Travel Products & Suppliers

available_seats is derived. booked_seats is updated by Dev 1 on confirm/cancel.
"""
from apps.tours.repositories import TourRepository


class TourService:
    def __init__(self, repository: TourRepository | None = None):
        self.repository = repository or TourRepository()

    def list_items(self):
        # TODO: replace with real list + pagination.
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
