"""
Finance does NOT have its own MongoDB collections.

OWNER: Dev 4 — Business Finance & Reports

Calculated (never stored as source of truth):
    Customer Balance = invoice totals - payments (+ refunds as agreed)
    Supplier Balance = expenses - supplier payments
    Accounts Receivable = sum of outstanding customer balances
    Accounts Payable = sum of outstanding supplier balances
    Tour Profit = tour revenue - tour expenses
    Net Profit = revenue - tour costs - general business expenses

Always exclude soft-deleted documents (`is_deleted: true`) from these sums.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from bson import ObjectId

from core.money import ZERO


@dataclass
class CustomerBalanceSnapshot:
    customer_id: ObjectId
    invoiced_total: Decimal = ZERO
    paid_total: Decimal = ZERO
    refunded_total: Decimal = ZERO
    balance: Decimal = ZERO


@dataclass
class SupplierBalanceSnapshot:
    supplier_id: ObjectId
    expense_total: Decimal = ZERO
    paid_total: Decimal = ZERO
    balance: Decimal = ZERO


@dataclass
class TourProfitabilitySnapshot:
    tour_id: ObjectId
    revenue: Decimal = ZERO
    expenses: Decimal = ZERO
    profit: Decimal = ZERO
    currency: Optional[str] = None
