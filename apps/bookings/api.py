import json
from unittest import result

from apps.bookings.services import BookingService
from core.exceptions import ValidationError
from core.responses import from_exception, success_response
from core.access import get_session_user


def _serialize_booking(booking: dict) -> dict:
    data = dict(booking)

    if "_id" in data:
        data["id"] = str(data.pop("_id"))

    for field in [
        "customer_id",
        "tour_id",
        "created_by",
        "updated_by",
        "deleted_by",
    ]:
        if field in data and data[field]:
            data[field] = str(data[field])

    for field in [
        "booking_date",
        "created_at",
        "updated_at",
        "deleted_at",
    ]:
        if data.get(field):
            data[field] = data[field].isoformat()

    if "pricing" in data and data["pricing"]:
        pricing = dict(data["pricing"])

        for field in [
            "unit_price",
            "subtotal",
            "discount_value",
            "discount_amount",
            "taxable_amount",
            "tax_rate",
            "tax_amount",
            "total_amount",
        ]:
            if field in pricing and pricing[field] is not None:
                pricing[field] = str(pricing[field])

        if pricing.get("discount_applied_by"):
            pricing["discount_applied_by"] = str(
                pricing["discount_applied_by"]
            )

        if pricing.get("tax_id"):
            pricing["tax_id"] = str(pricing["tax_id"])

        data["pricing"] = pricing

    return data

def list_bookings(request, **kwargs):
    service = BookingService()

    status = request.GET.get("status")
    customer_id = request.GET.get("customer_id")
    tour_id = request.GET.get("tour_id")

    include_deleted = (
        request.GET.get("include_deleted", "false").lower() == "true"
    )

    bookings = service.list_items(
        status=status,
        customer_id=customer_id,
        tour_id=tour_id,
        include_deleted=include_deleted,
    )

    items = []

    for booking in bookings:
     items.append(_serialize_booking(booking))

    return success_response({
        "items": items,
        "count": len(items),
    })

def create_booking(request, **kwargs):
    try:
        data = json.loads(request.body)

        service = BookingService()

        booking = service.create(data, user=get_session_user(request))

        result = _serialize_booking(booking)

        return success_response(result, status=201)

    except json.JSONDecodeError:
        return from_exception(
            ValidationError("Invalid JSON body.")
        )

    except Exception as exc:
     return from_exception(exc)

def get_booking(request, **kwargs):
    try:
        service = BookingService()
        booking = service.get_item(kwargs["id"])
        return success_response(_serialize_booking(booking))
    except Exception as exc:
        return from_exception(exc)

def patch_booking(request, **kwargs):
    try:
        data = json.loads(request.body)

        service = BookingService()
        booking = service.update(
            kwargs["id"],
            data,
            user=get_session_user(request),
        )

        return success_response(
            _serialize_booking(booking)
        )

    except json.JSONDecodeError:
        return from_exception(
            ValidationError("Invalid JSON body.")
        )
    except Exception as exc:
        return from_exception(exc)

def confirm_booking(request, **kwargs):
    try:
        service = BookingService()

        booking = service.confirm(
            kwargs["id"],
            user=get_session_user(request),
        )

        return success_response(
            _serialize_booking(booking)
        )

    except Exception as exc:
        return from_exception(exc)

def cancel_booking(request, **kwargs):
    try:
        service = BookingService()

        booking = service.cancel(
            kwargs["id"],
            user=get_session_user(request),
        )

        return success_response(
            _serialize_booking(booking)
        )

    except Exception as exc:
        return from_exception(exc)
