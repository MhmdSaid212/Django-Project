from apps.bookings.repositories import BookingRepository


class BookingService:
    def __init__(self, repository: BookingRepository | None = None):
        self.repository = repository or BookingRepository()

    def list_items(
        self,
        status: str | None = None,
        customer_id: str | None = None,
        tour_id: str | None = None,
        include_deleted: bool = False,
    ):
        return self.repository.find_all(
            status=status,
            customer_id=customer_id,
            tour_id=tour_id,
            include_deleted=include_deleted,
        )

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
