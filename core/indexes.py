"""
Recommended MongoDB indexes.

Call ensure_indexes() from a management command after schema work starts.
Email uniqueness applies to live rows only (soft-deleted emails can be reused).
Business numbers stay unique forever — never reuse CUS-1001 after a soft delete.
"""
from core.constants import Collections
from core.database import get_collection

# (collection, keys, unique, extra_options)
RECOMMENDED_INDEXES = [
    (Collections.USERS, [("email", 1)], True, {"partialFilterExpression": {"is_deleted": False}}),
    (Collections.CUSTOMERS, [("customer_number", 1)], True, None),
    (Collections.CUSTOMERS, [("email", 1)], True, {"partialFilterExpression": {"is_deleted": False}}),
    (Collections.SUPPLIERS, [("supplier_number", 1)], True, None),
    (Collections.TOURS, [("tour_code", 1)], True, None),
    (Collections.TOURS, [("package_id", 1)], False, None),
    (Collections.PACKAGES, [("package_code", 1)], True, None),
    (Collections.BOOKINGS, [("booking_number", 1)], True, None),
    (Collections.BOOKINGS, [("customer_id", 1)], False, None),
    (Collections.BOOKINGS, [("tour_id", 1)], False, None),
    (Collections.INVOICES, [("invoice_number", 1)], True, None),
    (Collections.INVOICES, [("booking_id", 1)], False, None),
    (Collections.PAYMENTS, [("payment_number", 1)], True, None),
    (Collections.PAYMENTS, [("invoice_id", 1)], False, None),
    (Collections.RECEIPTS, [("receipt_number", 1)], True, None),
    (Collections.REFUNDS, [("refund_number", 1)], True, None),
    (Collections.EXPENSES, [("expense_number", 1)], True, None),
    (Collections.SUPPLIER_PAYMENTS, [("supplier_payment_number", 1)], True, None),
    (Collections.AUDIT_LOGS, [("entity_type", 1), ("entity_id", 1)], False, None),
    (Collections.NOTIFICATIONS, [("user_id", 1), ("is_read", 1)], False, None),
    (Collections.TAXES, [("name", 1), ("effective_from", 1)], False, None),
    (Collections.TAXES, [("status", 1), ("effective_from", 1)], False, None),
    (Collections.ATTACHMENTS, [("entity_type", 1), ("entity_id", 1)], False, None),
]


def ensure_indexes() -> list[str]:
    created = []
    for collection_name, keys, unique, extra in RECOMMENDED_INDEXES:
        options = {"unique": unique}
        if extra:
            options.update(extra)
        get_collection(collection_name).create_index(keys, **options)
        created.append(f"{collection_name}: {keys} {options}")
    return created
