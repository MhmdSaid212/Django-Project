"""JSON API — invoices.  OWNER: Dev 3 — Customer Finance"""
import json

from apps.invoices.services import InvoiceService
from core.exceptions import TourOpsError, ValidationError
from core.permissions import get_session_user
from core.responses import from_exception, success_response


def _json_body(request) -> dict:
    if not request.body:
        return {}
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError as exc:
        raise ValidationError("Invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ValidationError("JSON object required.")
    return payload


def list_invoices(request, **kwargs):
    try:
        items = InvoiceService().list_items(
            customer_id=request.GET.get("customer_id"),
            status=request.GET.get("status"),
            booking_id=request.GET.get("booking_id"),
        )
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response({"invoices": items})


def create_invoice(request, **kwargs):
    """Generic create = create for a booking_id given in the body."""
    try:
        payload = _json_body(request)
        booking_id = payload.get("booking_id")
        if not booking_id:
            raise ValidationError("booking_id is required.")
        invoice = InvoiceService().create_for_booking(
            booking_id, created_by=get_session_user(request)["id"]
        )
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response(invoice, status=201)


def get_invoice(request, id=None, **kwargs):
    try:
        return success_response(InvoiceService().get(id))
    except TourOpsError as exc:
        return from_exception(exc)


def patch_invoice(request, id=None, **kwargs):
    try:
        payload = _json_body(request)
        action = payload.get("action")
        if action == "cancel":
            return success_response(InvoiceService().cancel(id))
        raise ValidationError("Unsupported patch. Send {\"action\": \"cancel\"}.")
    except TourOpsError as exc:
        return from_exception(exc)


def create_invoice_for_booking(request, booking_id=None, **kwargs):
    """POST /api/bookings/<booking_id>/invoice/ — the main invoicing path."""
    try:
        invoice = InvoiceService().create_for_booking(
            booking_id, created_by=get_session_user(request)["id"]
        )
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response(invoice, status=201)
