"""
MongoDB access for customers.

OWNER: Dev 1 — Customer & Booking Operations

Queries exclude soft-deleted rows by default. Never call delete_one().
"""
from pymongo.collection import Collection

from core.constants import Collections
from core.database import get_collection
from core.soft_delete import SoftDeleteRepositoryMixin


class CustomerRepository(SoftDeleteRepositoryMixin):
    def __init__(self, collection: Collection | None = None):
        self.collection = collection or get_collection(Collections.CUSTOMERS)
