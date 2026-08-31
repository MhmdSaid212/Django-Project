"""
MongoDB access for bookings.

OWNER: Dev 1 — Customer & Booking Operations

Do not hard-delete booking financial history. Use soft_delete().
"""
from pymongo.collection import Collection

from core.constants import Collections
from core.database import get_collection
from core.soft_delete import SoftDeleteRepositoryMixin


class BookingRepository(SoftDeleteRepositoryMixin):
    def __init__(self, collection: Collection | None = None):
        self.collection = collection or get_collection(Collections.BOOKINGS)
