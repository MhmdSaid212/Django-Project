import json

from apps.expenses.services import ExpenseService, serialize_expense
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


def _serialize_id(expense) -> dict:
    service = ExpenseService()
    return serialize_expense(service.get_presented(expense["_id"], include_payments=True))


def list_expenses(request, **kwargs):
    try:
        items = ExpenseService().list_presented(
            category=request.GET.get("category") or None,
            payment_status=request.GET.get("status") or request.GET.get("payment_status") or None,
            expense_scope=request.GET.get("scope") or request.GET.get("expense_scope") or None,
            supplier_id=request.GET.get("supplier_id") or None,
            tour_id=request.GET.get("tour_id") or None,
            overdue=request.GET.get("overdue") in {"1", "true", "yes"} or None,
        )
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response({"expenses": [serialize_expense(item) for item in items]})


def create_expense(request, **kwargs):
    try:
        payload = _json_body(request)
        expense = ExpenseService().create(
            actor_id=get_session_user(request)["id"],
            expense_scope=payload.get("expense_scope") or payload.get("scope") or "",
            category=payload.get("category") or "",
            amount=payload.get("amount"),
            description=payload.get("description") or "",
            expense_date=payload.get("expense_date"),
            currency=payload.get("currency"),
            supplier_id=payload.get("supplier_id"),
            tour_id=payload.get("tour_id"),
            due_date=payload.get("due_date"),
            receipt_file=payload.get("receipt_file"),
        )
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response(_serialize_id(expense), status=201)


def get_expense(request, **kwargs):
    try:
        record = ExpenseService().get_presented(kwargs.get("id"), include_payments=True)
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response(serialize_expense(record))


def patch_expense(request, **kwargs):
    try:
        payload = _json_body(request)
        changes = {
            key: payload[key]
            for key in (
                "expense_scope",
                "category",
                "amount",
                "description",
                "expense_date",
                "currency",
                "supplier_id",
                "tour_id",
                "due_date",
                "receipt_file",
            )
            if key in payload
        }
        if "scope" in payload and "expense_scope" not in changes:
            changes["expense_scope"] = payload["scope"]
        expense = ExpenseService().update(
            kwargs.get("id"),
            actor_id=get_session_user(request)["id"],
            **changes,
        )
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response(_serialize_id(expense))


def expenses_for_tour(request, **kwargs):
    try:
        items = ExpenseService().list_for_tour(kwargs.get("tour_id"))
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response({"expenses": [serialize_expense(item) for item in items]})


def expenses_for_supplier(request, **kwargs):
    try:
        items = ExpenseService().list_for_supplier(kwargs.get("id") or kwargs.get("supplier_id"))
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response({"expenses": [serialize_expense(item) for item in items]})
