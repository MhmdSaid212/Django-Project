"""
MongoDB access for payments.

OWNER: Dev 3 — Customer Finance

Never hard-delete a payment to represent a refund. Soft-delete is only for
removing a mistaken record from lists — the document stays in MongoDB.
"""
from pymongo.collection import Collection

from core.constants import Collections
from core.database import get_collection
from core.soft_delete import SoftDeleteRepositoryMixin


class PaymentRepository(SoftDeleteRepositoryMixin):
    def __init__(self, collection: Collection | None = None):
        self.collection = collection or get_collection(Collections.PAYMENTS)
