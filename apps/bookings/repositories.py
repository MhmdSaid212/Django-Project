from pymongo.collection import Collection

from core.constants import Collections
from core.database import get_collection
from core.soft_delete import SoftDeleteRepositoryMixin, live_query
from core.utils import parse_object_id


class BookingRepository(SoftDeleteRepositoryMixin):
    def __init__(self, collection: Collection | None = None):
        self.collection = collection or get_collection(Collections.BOOKINGS)

    def find_all(
        self,
        limit: int = 50,
        *,
        status: str | None = None,
        customer_id: str | None = None,
        tour_id: str | None = None,
        include_deleted: bool = False,
    ) -> list[dict]:

        filters = {}

        if status:
            filters["booking_status"] = status

        if customer_id:
            filters["customer_id"] = customer_id

        if tour_id:
            filters["tour_id"] = tour_id

        query_filter = (
            filters
            if include_deleted
            else live_query(filters)
        )

        return list(
            self.collection.find(query_filter).limit(limit)
        )

    def create(self, document: dict) -> dict:
        result = self.collection.insert_one(document)
        return self.collection.find_one({"_id": result.inserted_id})

    def find_by_id(self, booking_id: str) -> dict | None:
     oid = parse_object_id(booking_id, field="booking_id")

     return self.collection.find_one(
        live_query({"_id": oid})
    )


    def update_by_id(self, booking_id: str, updates: dict) -> dict | None:
        oid = parse_object_id(booking_id, field="booking_id")

        self.collection.update_one(
            live_query({"_id": oid}),
            {"$set": updates},
        )

        return self.collection.find_one(
            live_query({"_id": oid})
        )