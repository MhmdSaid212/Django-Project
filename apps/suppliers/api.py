from apps.suppliers.services import SupplierService, serialize_supplier
from core.http import actor_id, guarded, json_body, query_value, resource_id
from core.responses import success_response


def _presented(supplier) -> dict:
    return serialize_supplier(SupplierService().get_presented(supplier["_id"]))


@guarded
def list_suppliers(request, **kwargs):
    items = SupplierService().list_presented(
        supplier_type=query_value(request, "supplier_type", "type"),
        group=query_value(request, "group"),
        status=query_value(request, "status"),
    )
    return success_response({"suppliers": [serialize_supplier(item) for item in items]})


@guarded
def create_supplier(request, **kwargs):
    payload = json_body(request)
    supplier = SupplierService().create(
        actor_id=actor_id(request),
        name=payload.get("name") or "",
        supplier_type=payload.get("supplier_type") or payload.get("type") or "",
        **{key: value for key, value in payload.items() if key not in {"name", "supplier_type", "type"}},
    )
    return success_response(_presented(supplier), status=201)


@guarded
def get_supplier(request, **kwargs):
    record = SupplierService().get_presented(resource_id(kwargs))
    return success_response(serialize_supplier(record))


@guarded
def patch_supplier(request, **kwargs):
    payload = json_body(request)
    changes = dict(payload)
    if "type" in changes and "supplier_type" not in changes:
        changes["supplier_type"] = changes.pop("type")
    else:
        changes.pop("type", None)
    supplier = SupplierService().update(
        resource_id(kwargs),
        actor_id=actor_id(request),
        **changes,
    )
    return success_response(_presented(supplier))
