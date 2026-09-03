"""JSON API — refunds.  OWNER: Dev 3 — Customer Finance"""
import json

from apps.refunds.services import RefundService
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


def list_refunds(request, **kwargs):
    try:
        items = RefundService().list_items(
            customer_id=request.GET.get("customer_id"),
            status=request.GET.get("status"),
            payment_id=request.GET.get("payment_id"),
        )
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response({"refunds": items})


def create_refund(request, **kwargs):
    """Generic create = refund a payment_id given in the body."""
    try:
        payload = _json_body(request)
        payment_id = payload.get("payment_id")
        if not payment_id:
            raise ValidationError("payment_id is required.")
        refund = _create(request, payment_id, payload)
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response(refund, status=201)


def get_refund(request, id=None, **kwargs):
    try:
        return success_response(RefundService().get(id))
    except TourOpsError as exc:
        return from_exception(exc)


def refund_from_payment(request, payment_id=None, **kwargs):
    """POST /api/payments/<payment_id>/refund/ — the main refund path."""
    try:
        payload = _json_body(request)
        refund = _create(request, payment_id, payload)
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response(refund, status=201)


def approve_refund(request, id=None, **kwargs):
    try:
        result = RefundService().approve(id, actor_id=get_session_user(request)["id"])
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response(result)


def reject_refund(request, id=None, **kwargs):
    try:
        result = RefundService().reject(id, actor_id=get_session_user(request)["id"])
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response(result)


def complete_refund(request, id=None, **kwargs):
    try:
        result = RefundService().complete(id, actor_id=get_session_user(request)["id"])
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response(result)


def _create(request, payment_id, payload):
    return RefundService().create_from_payment(
        payment_id,
        reason=payload.get("reason") or "",
        refund_method=payload.get("refund_method") or "CASH",
        tier=payload.get("policy_tier"),
        days_before=payload.get("days_before"),
        amount=payload.get("amount"),
        requested_by=get_session_user(request)["id"],
    )
