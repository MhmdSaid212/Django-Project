"""
MongoDB access for suppliers.

OWNER: Dev 2 — Travel Products & Suppliers

Type-specific details live in hotel_info / transportation_info / tour_guide_info, etc.
Queries exclude soft-deleted rows by default. Never call delete_one().
"""
from pymongo.collection import Collection

from core.constants import Collections
from core.database import get_collection
from core.soft_delete import SoftDeleteRepositoryMixin


class SupplierRepository(SoftDeleteRepositoryMixin):
    def __init__(self, collection: Collection | None = None):
        self.collection = collection or get_collection(Collections.SUPPLIERS)
