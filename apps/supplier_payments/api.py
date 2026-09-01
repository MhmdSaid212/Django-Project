import json

from apps.supplier_payments.services import SupplierPaymentService, serialize_payment
from core.exceptions import TourOpsError, ValidationError
from core.permissions import get_session_user
from core.responses import from_exception, success_response


def _json_body(request) -> dict:
    if not request.body:
        return {}
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError as extra:
        raise ValidationError("Invalid JSON.") from extra
    if not isinstance(payload, dict):
        raise ValidationError("JSON object required.")
    return payload


def _presented(payment: dict) -> dict:
    return serialize_payment(SupplierPaymentService().get_presented(payment["_id"]))


def list_supplier_payments(request, **kwargs):
    try:
        items = SupplierPaymentService().list_presented(
            supplier_id=request.GET.get("supplier_id") or None,
            expense_id=request.GET.get("expense_id") or None,
        )
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response({"payments": [serialize_payment(item) for item in items]})


def create_supplier_payment(request, **kwargs):
    try:
        payload = _json_body(request)
        payment = SupplierPaymentService().create(
            actor_id=get_session_user(request)["id"],
            expense_id=payload.get("expense_id"),
            amount=payload.get("amount"),
            payment_method=payload.get("payment_method") or payload.get("method") or "",
            payment_date=payload.get("payment_date"),
            reference_number=payload.get("reference_number") or payload.get("ref"),
            notes=payload.get("notes"),
            currency=payload.get("currency"),
            supplier_id=payload.get("supplier_id"),
        )
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response(_presented(payment), status=201)


def get_supplier_payment(request, **kwargs):
    try:
        record = SupplierPaymentService().get_presented(kwargs.get("id"))
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response(serialize_payment(record))


def supplier_payments_for_supplier(request, **kwargs):
    try:
        items = SupplierPaymentService().list_for_supplier(kwargs.get("supplier_id") or kwargs.get("id"))
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response({"payments": [serialize_payment(item) for item in items]})


def create_supplier_payment_for_supplier(request, **kwargs):
    try:
        payload = _json_body(request)
        payment = SupplierPaymentService().create(
            actor_id=get_session_user(request)["id"],
            expense_id=payload.get("expense_id"),
            amount=payload.get("amount"),
            payment_method=payload.get("payment_method") or payload.get("method") or "",
            payment_date=payload.get("payment_date"),
            reference_number=payload.get("reference_number") or payload.get("ref"),
            notes=payload.get("notes"),
            currency=payload.get("currency"),
            supplier_id=kwargs.get("supplier_id") or kwargs.get("id"),
        )
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response(_presented(payment), status=201)
