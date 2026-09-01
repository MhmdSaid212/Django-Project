import json

from apps.packages.services import PackageService, serialize_package
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


def _presented(package) -> dict:
    return serialize_package(PackageService().get_presented(package["_id"]))


def list_packages(request, **kwargs):
    try:
        items = PackageService().list_presented(status=request.GET.get("status") or None)
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response({"packages": [serialize_package(item) for item in items]})


def create_package(request, **kwargs):
    try:
        payload = _json_body(request)
        package = PackageService().create(actor_id=get_session_user(request)["id"], **payload)
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response(_presented(package), status=201)


def get_package(request, **kwargs):
    try:
        record = PackageService().get_presented(kwargs.get("id"))
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response(serialize_package(record))


def patch_package(request, **kwargs):
    try:
        payload = _json_body(request)
        if "price" in payload and "selling_price_per_person" not in payload:
            payload["selling_price_per_person"] = payload.pop("price")
        package = PackageService().update(
            kwargs.get("id"),
            actor_id=get_session_user(request)["id"],
            **payload,
        )
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response(_presented(package))
