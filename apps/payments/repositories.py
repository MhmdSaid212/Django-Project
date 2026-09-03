"""MongoDB access for payments.  OWNER: Dev 3 — Customer Finance"""
from __future__ import annotations

from pymongo.collection import Collection

from core.constants import Collections, PaymentRecordStatus
from core.database import get_collection
from core.soft_delete import SoftDeleteRepositoryMixin, live_query
from core.utils import parse_object_id


class PaymentRepository(SoftDeleteRepositoryMixin):
    def __init__(self, collection: Collection | None = None):
        self.collection = collection or get_collection(Collections.PAYMENTS)

    def list_payments(self, *, invoice_id=None, customer_id=None, limit: int = 100) -> list[dict]:
        query: dict = {}
        if invoice_id:
            query["invoice_id"] = parse_object_id(invoice_id, field="invoice_id")
        if customer_id:
            query["customer_id"] = parse_object_id(customer_id, field="customer_id")
        return list(self.collection.find(live_query(query)).sort("created_at", -1).limit(limit))

    def find_for_invoice(self, invoice_id) -> list[dict]:
        return list(self.collection.find(live_query({
            "invoice_id": parse_object_id(invoice_id, field="invoice_id"),
        })).sort("created_at", 1))

    def mark_voided(self, payment_id) -> None:
        from core.utils import utcnow
        self.collection.update_one(
            live_query({"_id": parse_object_id(payment_id, field="payment_id")}),
            {"$set": {"status": PaymentRecordStatus.VOIDED.value, "updated_at": utcnow()}},
        )
