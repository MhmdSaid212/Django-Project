import json

from apps.suppliers.services import SupplierService, serialize_supplier
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


def _presented(supplier) -> dict:
    return serialize_supplier(SupplierService().get_presented(supplier["_id"]))


def list_suppliers(request, **kwargs):
    try:
        items = SupplierService().list_presented(
            supplier_type=request.GET.get("supplier_type") or request.GET.get("type") or None,
            group=request.GET.get("group") or None,
            status=request.GET.get("status") or None,
        )
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response({"suppliers": [serialize_supplier(item) for item in items]})


def create_supplier(request, **kwargs):
    try:
        payload = _json_body(request)
        supplier = SupplierService().create(
            actor_id=get_session_user(request)["id"],
            name=payload.get("name") or "",
            supplier_type=payload.get("supplier_type") or payload.get("type") or "",
            **{
                key: value
                for key, value in payload.items()
                if key not in {"name", "supplier_type", "type"}
            },
        )
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response(_presented(supplier), status=201)


def get_supplier(request, **kwargs):
    try:
        record = SupplierService().get_presented(kwargs.get("id"))
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response(serialize_supplier(record))


def patch_supplier(request, **kwargs):
    try:
        payload = _json_body(request)
        changes = dict(payload)
        if "type" in changes and "supplier_type" not in changes:
            changes["supplier_type"] = changes.pop("type")
        else:
            changes.pop("type", None)
        supplier = SupplierService().update(
            kwargs.get("id"),
            actor_id=get_session_user(request)["id"],
            **changes,
        )
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response(_presented(supplier))
