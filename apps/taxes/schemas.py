"""
Tax document contract. NOT a Django model.

OWNER: Platform / Owner-Admin
Collection: taxes

BR-TAX-01: multiple named taxes with percentage, effective date, and
ACTIVE/INACTIVE. Example: "VAT 11%" from 2026-01-01 vs a later rate.

system_settings.default_tax_id points at the current default.
Bookings and invoices snapshot tax name, rate, and amount at issue time
(optional tax_id). Changing a tax later must not rewrite issued invoices.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from bson import ObjectId

from core.constants import TaxStatus


@dataclass
class TaxDocument:
    name: str
    rate: Decimal
    effective_from: datetime
    created_by: ObjectId
    created_at: datetime
    updated_at: datetime
    effective_to: Optional[datetime] = None
    status: str = TaxStatus.ACTIVE.value
    updated_by: Optional[ObjectId] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[ObjectId] = None
    _id: Optional[ObjectId] = None
