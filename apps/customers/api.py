import json
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from django.http import JsonResponse

from apps.customers.services import CustomerService
from apps.customers.validators import validate_customer_data
from core.permissions import get_session_user
from core.responses import error_response, success_response


def _serialize_customer(customer):
    if not customer:
        return None

    data = dict(customer)

    if "_id" in data:
        data["id"] = str(data.pop("_id"))

    if "created_by" in data:
        data["created_by"] = str(data["created_by"])

    if "deleted_by" in data and data["deleted_by"]:
        data["deleted_by"] = str(data["deleted_by"])

    if data.get("date_of_birth"):
        data["date_of_birth"] = data["date_of_birth"].isoformat()

    if data.get("created_at"):
        data["created_at"] = data["created_at"].isoformat()

    if data.get("updated_at"):
        data["updated_at"] = data["updated_at"].isoformat()

    if data.get("deleted_at"):
        data["deleted_at"] = data["deleted_at"].isoformat()

    return data


def list_customers(request, **kwargs):
    service = CustomerService()

    query = request.GET.get("q")
    status = request.GET.get("status")

    include_deleted = (
        request.GET.get("include_deleted", "false").lower() == "true"
    )

    customers = service.list_items(
        query=query,
        status=status,
        include_deleted=include_deleted,
    )

    items = [_serialize_customer(customer) for customer in customers]

    return success_response({
        "items": items,
        "count": len(items),
    })


def create_customer(request, **kwargs):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return error_response(
            "VALIDATION_ERROR",
            "Invalid JSON request body.",
        )

    # Validate the incoming data
    is_valid, errors = validate_customer_data(data)

    if not is_valid:
        return error_response(
        "VALIDATION_ERROR",
        "Invalid customer data.",
        extra={"fields": errors},
    )

    # Convert date_of_birth from JSON string to datetime
    date_of_birth = data.get("date_of_birth")

    if date_of_birth:
        try:
            date_of_birth = datetime.fromisoformat(
    str(date_of_birth)
).replace(tzinfo=timezone.utc)
        except ValueError:
            return error_response(
                "VALIDATION_ERROR",
                "date_of_birth must be a valid ISO-8601 date.",
            )

    service = CustomerService()

    try:
        customer = service.create(
            data=data,
            date_of_birth=date_of_birth,
            user=get_session_user(request),
        )

        return success_response(
            _serialize_customer(customer),
            status=201,
        )

    except ValueError as exc:
        return error_response(
            "CONFLICT",
            str(exc),
            status=409,
        )

    except Exception:
        return error_response(
            "INTERNAL_ERROR",
            "An unexpected error occurred.",
            status=500,
        )

def get_customer(request, id, **kwargs):
    service = CustomerService()

    try:
        customer = service.get(id)

        if not customer:
            return error_response(
                "NOT_FOUND",
                "Customer not found.",
                status=404,
            )

        return success_response(
            _serialize_customer(customer)
        )

    except (InvalidId, ValueError):
        return error_response(
            "NOT_FOUND",
            "Customer not found.",
            status=404,
        )


def patch_customer(request, id, **kwargs):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return error_response(
            "VALIDATION_ERROR",
            "Invalid JSON request body.",
        )

    if not isinstance(data, dict):
        return error_response(
            "VALIDATION_ERROR",
            "Request body must be a JSON object.",
        )

    service = CustomerService()

    try:
        customer = service.get(id)

        if not customer:
            return error_response(
                "NOT_FOUND",
                "Customer not found.",
                status=404,
            )

        # Soft delete
        if data.get("is_deleted") is True:
            user = get_session_user(request)

            if not user or not user.get("id"):
                return error_response(
                    "UNAUTHENTICATED",
                    "Login required.",
                    status=401,
                )

            service.repository.soft_delete(
                id,
                user["id"],
            )

            customer = service.repository.find_by_id(
                id,
                include_deleted=True,
            )

            return success_response(
                _serialize_customer(customer)
            )

        # Restore
        if data.get("is_deleted") is False:
            customer = service.repository.restore(id)

            if not customer:
                return error_response(
                    "NOT_FOUND",
                    "Customer not found.",
                    status=404,
                )

            return success_response(
                _serialize_customer(customer)
            )

        # Normal update
        validation_data = dict(data)

        valid, errors = validate_customer_data(
        validation_data,
        partial=True,
)

        if not valid:
         return error_response(
          "VALIDATION_ERROR",
           "Invalid customer data.",
           extra={"fields": errors},
    )
        # Convert DOB if supplied
        date_of_birth = validation_data.get("date_of_birth")

        if date_of_birth:
            try:
                validation_data["date_of_birth"] = datetime.fromisoformat(
                    date_of_birth
                ).replace(tzinfo=timezone.utc)
            except ValueError:
                return error_response(
                    "VALIDATION_ERROR",
                    "date_of_birth must be a valid ISO-8601 date.",
                )

        updated = service.update(
            id,
            validation_data,
            user=get_session_user(request),
        )

        return success_response(
            _serialize_customer(updated)
        )

    except InvalidId:
        return error_response(
            "NOT_FOUND",
            "Customer not found.",
            status=404,
        )

    except ValueError as exc:
        return error_response(
            "CONFLICT",
            str(exc),
            status=409,
        )
