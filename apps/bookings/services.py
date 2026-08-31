"""
Business rules.

OWNER: Dev 1 — Customer & Booking Operations

Confirm/cancel must update tour.booked_seats. Do not delete financial history.
"""
from apps.bookings.repositories import BookingRepository


class BookingService:
    def __init__(self, repository: BookingRepository | None = None):
        self.repository = repository or BookingRepository()

    def list_items(self):
        # TODO: replace with real list + pagination.
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
