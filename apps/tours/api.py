import json

from apps.tours.services import TourService, serialize_tour
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


def _presented(tour) -> dict:
    return serialize_tour(TourService().get_presented(tour["_id"]))


def list_tours(request, **kwargs):
    try:
        items = TourService().list_presented(
            status=request.GET.get("status") or None,
            package_id=request.GET.get("package_id") or None,
        )
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response({"tours": [serialize_tour(item) for item in items]})


def create_tour(request, **kwargs):
    try:
        payload = _json_body(request)
        if "price" in payload and "selling_price_per_person" not in payload:
            payload["selling_price_per_person"] = payload.pop("price")
        tour = TourService().create(actor_id=get_session_user(request)["id"], **payload)
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response(_presented(tour), status=201)


def get_tour(request, **kwargs):
    try:
        record = TourService().get_presented(kwargs.get("id"))
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response(serialize_tour(record))


def patch_tour(request, **kwargs):
    try:
        payload = _json_body(request)
        if "price" in payload and "selling_price_per_person" not in payload:
            payload["selling_price_per_person"] = payload.pop("price")
        tour = TourService().update(
            kwargs.get("id"),
            actor_id=get_session_user(request)["id"],
            **payload,
        )
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response(_presented(tour))


def tour_availability(request, **kwargs):
    try:
        record = TourService().get_presented(kwargs.get("id"), include_extras=False)
    except TourOpsError as extra:
        return from_exception(extra)
    return success_response(
        {
            "id": record["id"],
            "code": record["code"],
            "name": record["name"],
            "capacity": record["capacity"],
            "booked": record["booked"],
            "available": record["available"],
            "pct": record["pct"],
            "status": record["status"],
            "dates": record["dates"],
        }
    )
