"""
Supplier payment document contract. NOT a Django model.

OWNER: Dev 4 — Business Finance & Reports
Collection: supplier_payments
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from bson import ObjectId


@dataclass
class SupplierPaymentDocument:
    supplier_payment_number: str
    supplier_id: ObjectId
    expense_id: ObjectId
    amount: Decimal
    currency: str
    payment_method: str
    payment_date: datetime
    recorded_by: ObjectId
    created_at: datetime
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[ObjectId] = None
    _id: Optional[ObjectId] = None
