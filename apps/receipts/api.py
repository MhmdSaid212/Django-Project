"""JSON API — receipts.  OWNER: Dev 3 — Customer Finance

No POST endpoint: receipts are auto-created when a payment completes.
"""
from apps.receipts.services import ReceiptService
from core.exceptions import TourOpsError
from core.responses import from_exception, success_response


def get_receipt(request, id=None, **kwargs):
    try:
        return success_response(ReceiptService().get(id))
    except TourOpsError as exc:
        return from_exception(exc)


def receipt_for_payment(request, payment_id=None, **kwargs):
    try:
        return success_response(ReceiptService().for_payment(payment_id))
    except TourOpsError as exc:
        return from_exception(exc)
