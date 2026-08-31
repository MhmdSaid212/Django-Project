from apps.bookings.repositories import BookingRepository


class BookingService:
    def __init__(self, repository: BookingRepository | None = None):
        self.repository = repository or BookingRepository()

    def list_items(self):
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
