"""
Invoice business rules.  OWNER: Dev 3 — Customer Finance

Rules enforced here:
- Only a CONFIRMED booking can be invoiced (Dev 1 owns the booking).
- One live invoice per booking (second attempt -> CONFLICT).
- taxable_amount = subtotal - discount.amount ; total = taxable + tax.amount
- Status is DERIVED from paid/refunded amounts, never set to PAID by hand.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from bson import ObjectId

from apps.invoices.repositories import InvoiceRepository
from core.constants import Collections, InvoiceStatus
from core.database import get_collection
from core.exceptions import NotFoundError, TourOpsError, ValidationError
from core.money import ZERO, to_decimal, to_decimal128, to_money
from core.numbering import next_number
from core.soft_delete import stamp_new
from core.utils import parse_object_id, serialize_id, utcnow


class ConflictError(TourOpsError):
    code = "CONFLICT"
    http_status = 409


class BusinessRuleViolation(TourOpsError):
    code = "BUSINESS_RULE_VIOLATION"
    http_status = 422


def compute_status(total: Decimal, paid: Decimal, refunded: Decimal) -> str:
    """Derive invoice status from money only. Never set PAID manually."""
    net = paid - refunded
    if net <= ZERO:
        return InvoiceStatus.ISSUED.value
    if net < total:
        return InvoiceStatus.PARTIALLY_PAID.value
    return InvoiceStatus.PAID.value


def _full_name(customer: dict) -> str:
    """Build a display name from a customer document."""
    first = (customer.get("first_name") or "").strip()
    last = (customer.get("last_name") or "").strip()
    return (first + " " + last).strip() or None


def present_invoice(doc: dict) -> dict:
    """Convert a raw Mongo invoice into a JSON-safe dict."""
    if not doc:
        return {}
    money = lambda k: str(to_money(doc.get(k, 0)))
    return {
        "id": serialize_id(doc.get("_id")),
        "invoice_number": doc.get("invoice_number"),
        "booking_id": serialize_id(doc.get("booking_id")),
        "booking_number": doc.get("booking_number"),
        "customer_id": serialize_id(doc.get("customer_id")),
        "customer_name": doc.get("customer_name"),
        "customer_email": doc.get("customer_email"),
        "issue_date": doc.get("issue_date"),
        "due_date": doc.get("due_date"),
        "line_items": doc.get("line_items", []),
        "subtotal": money("subtotal"),
        "taxable_amount": money("taxable_amount"),
        "total_amount": money("total_amount"),
        "paid_amount": money("paid_amount"),
        "refunded_amount": money("refunded_amount"),
        "remaining_amount": money("remaining_amount"),
        "status": doc.get("status"),
    }


class InvoiceService:
    def __init__(self, repository: InvoiceRepository | None = None):
        self.repository = repository or InvoiceRepository()

    # ---- reads -------------------------------------------------------------
    def list_items(self, **filters) -> list[dict]:
        return [present_invoice(d) for d in self.repository.list_invoices(**filters)]

    def get(self, doc_id: str) -> dict:
        doc = self.repository.find_by_id(doc_id)
        if not doc:
            raise NotFoundError("Invoice not found.")
        return present_invoice(doc)

    def _get_raw(self, doc_id: str) -> dict:
        doc = self.repository.find_by_id(doc_id)
        if not doc:
            raise NotFoundError("Invoice not found.")
        return doc

    # ---- create from a confirmed booking (the main path) -------------------
    def create_for_booking(self, booking_id: str, *, created_by: str, due_days: int = 14) -> dict:
        booking = get_collection(Collections.BOOKINGS).find_one(
            {"_id": parse_object_id(booking_id, field="booking_id"), "is_deleted": {"$ne": True}}
        )
        if not booking:
            raise NotFoundError("Booking not found.")
        if booking.get("booking_status") != "CONFIRMED":
            raise BusinessRuleViolation("Only a CONFIRMED booking can be invoiced.")

        existing = self.repository.find_by_booking(booking_id)
        if existing:
            raise ConflictError("This booking already has a live invoice.")

        # Denormalize display fields (ERD DN pattern): copy the customer's name and
        # the booking number onto the invoice so list/detail screens never need a join.
        customer = None
        if booking.get("customer_id"):
            customer = get_collection(Collections.CUSTOMERS).find_one(
                {"_id": booking["customer_id"], "is_deleted": {"$ne": True}}
            )
        customer_name = _full_name(customer) if customer else None
        customer_email = (customer or {}).get("email")

        pricing = booking.get("pricing", {})
        subtotal = to_decimal(pricing.get("subtotal", 0))
        discount_amount = to_decimal(pricing.get("discount_amount", 0))
        taxable = to_money(subtotal - discount_amount)
        tax_amount = to_decimal(pricing.get("tax_amount", 0))
        total = to_money(taxable + tax_amount)

        now = utcnow()
        doc = stamp_new({
            "invoice_number": next_number(Collections.INVOICES),
            "booking_id": booking["_id"],
            "booking_number": booking.get("booking_number"),
            "customer_id": booking.get("customer_id"),
            "customer_name": customer_name,
            "customer_email": customer_email,
            "issue_date": now,
            "due_date": now + timedelta(days=due_days),
            "line_items": [{
                "description": booking.get("notes") or "Tour booking",
                "quantity": int(booking.get("travelers_count", 1)),
                "unit_price": to_decimal128(pricing.get("unit_price", 0)),
                "total": to_decimal128(subtotal),
            }],
            "subtotal": to_decimal128(subtotal),
            "discount": {
                "type": pricing.get("discount_type", "NONE"),
                "value": to_decimal128(pricing.get("discount_value", 0)),
                "amount": to_decimal128(discount_amount),
                "reason": pricing.get("discount_reason"),
                "applied_by": pricing.get("discount_applied_by"),
            },
            "taxable_amount": to_decimal128(taxable),
            "tax": {
                "name": "VAT",
                "rate": to_decimal128(pricing.get("tax_rate", 0)),
                "amount": to_decimal128(tax_amount),
                "tax_id": pricing.get("tax_id"),
            },
            "total_amount": to_decimal128(total),
            "paid_amount": to_decimal128(ZERO),
            "refunded_amount": to_decimal128(ZERO),
            "remaining_amount": to_decimal128(total),
            "status": InvoiceStatus.ISSUED.value,
            "created_by": parse_object_id(created_by, field="created_by"),
            "created_at": now,
            "updated_at": now,
        })
        result = self.repository.insert(doc)
        doc["_id"] = result.inserted_id
        return present_invoice(doc)

    def cancel(self, doc_id: str) -> dict:
        doc = self._get_raw(doc_id)
        if to_decimal(doc.get("paid_amount", 0)) > ZERO:
            raise BusinessRuleViolation("A paid invoice cannot be cancelled. Record a refund instead.")
        self.repository.update(doc_id, {"status": InvoiceStatus.CANCELLED.value})
        return self.get(doc_id)

    # ---- rollup recompute, called by PaymentService/RefundService ----------
    def recompute_rollups(self, invoice_id: str) -> dict:
        """Recalculate paid/refunded/remaining/status from payment + refund docs."""
        inv = self._get_raw(invoice_id)
        oid = inv["_id"]
        total = to_decimal(inv.get("total_amount", 0))

        payments = get_collection(Collections.PAYMENTS).aggregate([
            {"$match": {"invoice_id": oid, "status": "COMPLETED", "is_deleted": {"$ne": True}}},
            {"$group": {"_id": None, "sum": {"$sum": "$amount"}}},
        ])
        paid = to_decimal(next(iter(payments), {}).get("sum", 0))

        refunds = get_collection(Collections.REFUNDS).aggregate([
            {"$match": {"invoice_id": oid, "status": "COMPLETED", "is_deleted": {"$ne": True}}},
            {"$group": {"_id": None, "sum": {"$sum": "$amount"}}},
        ])
        refunded = to_decimal(next(iter(refunds), {}).get("sum", 0))

        remaining = to_money(total - paid + refunded)
        status = compute_status(total, paid, refunded)

        self.repository.set_rollups(
            invoice_id,
            paid=to_decimal128(paid),
            refunded=to_decimal128(refunded),
            remaining=to_decimal128(remaining),
            status=status,
        )
        return {
            "invoice_id": serialize_id(oid),
            "total": str(to_money(total)),
            "paid": str(to_money(paid)),
            "refunded": str(to_money(refunded)),
            "remaining": str(remaining),
            "status": status,
        }
