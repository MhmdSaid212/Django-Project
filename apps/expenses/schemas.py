"""
Expense document contract. NOT a Django model.

OWNER: Dev 4 — Business Finance & Reports
Collection: expenses

Expense = cost incurred.
Supplier payment = money actually paid.
They are not the same thing.

Operational trip costs attach to a tour (the dated package run), not to the
package template. Use expense_scope GENERAL for overhead with no tour.

Example: Expense 3000, Supplier Payment 2000, Remaining Payable 1000.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from bson import ObjectId

from core.constants import ExpenseCategory, ExpensePaymentStatus, ExpenseScope
from core.money import ZERO


@dataclass
class ExpenseDocument:
    expense_number: str
    expense_scope: str  # ExpenseScope: TOUR or GENERAL
    category: str  # ExpenseCategory
    amount: Decimal
    currency: str
    description: str
    expense_date: datetime
    created_by: ObjectId
    created_at: datetime
    updated_at: datetime
    supplier_id: Optional[ObjectId] = None
    tour_id: Optional[ObjectId] = None
    due_date: Optional[datetime] = None
    paid_amount: Decimal = ZERO
    remaining_amount: Decimal = ZERO
    payment_status: str = ExpensePaymentStatus.UNPAID.value
    receipt_file: Optional[str] = None  # shortcut; files live in attachments
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[ObjectId] = None
    _id: Optional[ObjectId] = None
