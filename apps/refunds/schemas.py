"""
Refund document contract. NOT a Django model.

OWNER: Dev 3 — Customer Finance
Collection: refunds

A refund is a new document. The original payment stays.
Example: Payment +800, Refund -300 — both records remain.

Policy audit (BR-REF-04–08): store which tier, policy version, percent,
deposit excluded, and retained fee — do not rely on free-text `reason`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from bson import ObjectId

from core.constants import RefundPolicyTier, RefundStatus
from core.money import ZERO


@dataclass
class RefundDocument:
    refund_number: str
    customer_id: ObjectId
    booking_id: ObjectId
    invoice_id: ObjectId
    payment_id: ObjectId
    amount: Decimal
    reason: str
    refund_method: str
    created_at: datetime
    status: str = RefundStatus.PENDING.value
    policy_tier: str = RefundPolicyTier.OTHER.value
    policy_version: Optional[str] = None
    refund_percent: Optional[Decimal] = None
    deposit_excluded_amount: Decimal = ZERO
    retained_fee_amount: Decimal = ZERO
    approved_at: Optional[datetime] = None
    approved_by: Optional[ObjectId] = None
    processed_at: Optional[datetime] = None
    processed_by: Optional[ObjectId] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[ObjectId] = None
    _id: Optional[ObjectId] = None
