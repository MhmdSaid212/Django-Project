"""JSON API — payments.  OWNER: Dev 3 — Customer Finance"""
import json

from apps.payments.services import PaymentService
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


def list_payments(request, **kwargs):
    try:
        items = PaymentService().list_items(
            invoice_id=request.GET.get("invoice_id"),
            customer_id=request.GET.get("customer_id"),
        )
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response({"payments": items})


def create_payment(request, **kwargs):
    """Generic create = pay an invoice_id given in the body."""
    try:
        payload = _json_body(request)
        invoice_id = payload.get("invoice_id")
        if not invoice_id:
            raise ValidationError("invoice_id is required.")
        payment = _record(request, invoice_id, payload)
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response(payment, status=201)


def get_payment(request, id=None, **kwargs):
    try:
        return success_response(PaymentService().get(id))
    except TourOpsError as exc:
        return from_exception(exc)


def payments_for_invoice(request, invoice_id=None, **kwargs):
    try:
        return success_response({"payments": PaymentService().for_invoice(invoice_id)})
    except TourOpsError as exc:
        return from_exception(exc)


def create_payment_for_invoice(request, invoice_id=None, **kwargs):
    """POST /api/invoices/<invoice_id>/payments/ — the main pay path."""
    try:
        payload = _json_body(request)
        payment = _record(request, invoice_id, payload)
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response(payment, status=201)


def void_payment(request, payment_id=None, **kwargs):
    """POST /api/payments/<payment_id>/void/ — correct a recording error."""
    try:
        result = PaymentService().void(payment_id, actor_id=get_session_user(request)["id"])
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response(result)


def _record(request, invoice_id, payload):
    return PaymentService().record_for_invoice(
        invoice_id,
        amount=payload.get("amount"),
        method=payload.get("payment_method") or payload.get("method"),
        reference_number=payload.get("reference_number"),
        notes=payload.get("notes"),
        recorded_by=get_session_user(request)["id"],
    )
