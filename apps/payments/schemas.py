"""
Payment document contract. NOT a Django model.

OWNER: Dev 3 — Customer Finance
Collection: payments

Never delete a payment to represent a refund. Keep both records.
Soft-delete is only for hiding a mistaken payment from lists — it is not a refund.
Do not allow payment greater than remaining invoice balance unless
overpayment is explicitly added later.

Invoice payment_status rollup:
    paid == 0            → UNPAID
    0 < paid < total     → PARTIALLY_PAID
    paid >= total        → PAID
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from bson import ObjectId

from core.constants import PaymentMethod, PaymentRecordStatus
from core.money import ZERO


@dataclass
class PaymentDocument:
    payment_number: str
    invoice_id: ObjectId
    booking_id: ObjectId
    customer_id: ObjectId
    amount: Decimal
    currency: str
    payment_method: str  # PaymentMethod
    payment_date: datetime
    recorded_by: ObjectId
    created_at: datetime
    reference_number: Optional[str] = None
    status: str = PaymentRecordStatus.COMPLETED.value
    notes: Optional[str] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[ObjectId] = None
    _id: Optional[ObjectId] = None
