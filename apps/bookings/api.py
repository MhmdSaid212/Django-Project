from apps.bookings.services import BookingService
from core.responses import success_response


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
        data = dict(booking)

        if "_id" in data:
            data["id"] = str(data.pop("_id"))

        if "customer_id" in data:
            data["customer_id"] = str(data["customer_id"])

        if "tour_id" in data:
            data["tour_id"] = str(data["tour_id"])

        if "created_by" in data:
            data["created_by"] = str(data["created_by"])

        if "updated_by" in data:
            data["updated_by"] = str(data["updated_by"])

        if "deleted_by" in data and data["deleted_by"]:
            data["deleted_by"] = str(data["deleted_by"])

        for field in [
            "booking_date",
            "created_at",
            "updated_at",
            "deleted_at",
        ]:
            if data.get(field):
                data[field] = data[field].isoformat()

        # Convert Decimal values inside pricing
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

        items.append(data)

    return success_response({
        "items": items,
        "count": len(items),
    })

def create_booking(request, **kwargs):
 return not_implemented("POST /api/bookings/ is not implemented yet. Owner: Dev 1.")

def get_booking(request, **kwargs):
 return not_implemented("GET /api/bookings/<id>/ is not implemented yet. Owner: Dev 1.")

def patch_booking(request, **kwargs):
 return not_implemented("PATCH /api/bookings/<id>/ is not implemented yet. Owner: Dev 1.")

def confirm_booking(request, **kwargs):
 return not_implemented("POST /api/bookings/<id>/confirm/ is not implemented yet. Owner: Dev 1.")

def cancel_booking(request, **kwargs):
 return not_implemented("POST /api/bookings/<id>/cancel/ is not implemented yet. Owner: Dev 1.")
