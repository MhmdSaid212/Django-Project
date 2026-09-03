from __future__ import annotations

from apps.packages.validators import parse_positive_int
from apps.supplier_reservations.constants import DEFAULT_OCCUPANCY, ROOM_TYPE_LABELS
from core.constants import SupplierReservationStatus, SupplierType
from core.exceptions import ValidationError


def validate_status(value: str) -> str:
    status = (value or "").strip().upper()
    if status not in {item.value for item in SupplierReservationStatus}:
        raise ValidationError("Invalid reservation status.")
    return status


def validate_service_type(value: str) -> str:
    service_type = (value or "").strip().upper()
    if service_type not in {item.value for item in SupplierType}:
        raise ValidationError("Invalid service type.")
    return service_type


def validate_room_type(value: str) -> str:
    room_type = (value or "").strip().upper()
    if room_type not in ROOM_TYPE_LABELS:
        raise ValidationError("Invalid room type.")
    return room_type


def occupancy_for(room_type: str, occupancy=None) -> int:
    if occupancy in (None, ""):
        return DEFAULT_OCCUPANCY.get(room_type, 1)
    number = parse_positive_int(occupancy, field="occupancy")
    return number


def clean_room_allocations(raw) -> list[dict]:
    if raw in (None, ""):
        return []
    if not isinstance(raw, list):
        raise ValidationError("Room allocations must be a list.")
    lines = []
    seen = set()
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValidationError(f"Allocation {index} is invalid.")
        room_type = (item.get("room_type") or item.get("type") or "").strip()
        quantity = item.get("quantity")
        if room_type in (None, "") and quantity in (None, "", 0, "0"):
            continue
        room_type = validate_room_type(room_type)
        quantity = parse_positive_int(quantity, field="quantity")
        occupancy = occupancy_for(room_type, item.get("occupancy"))
        if occupancy < 1:
            raise ValidationError(f"Allocation {index}: occupancy must be at least 1.")
        if room_type in seen:
            raise ValidationError(f"Room type {room_type} is listed twice.")
        seen.add(room_type)
        lines.append({"room_type": room_type, "quantity": quantity, "occupancy": occupancy})
    return lines


def bed_capacity(allocations: list[dict]) -> int:
    total = 0
    for line in allocations or []:
        total += int(line.get("quantity") or 0) * int(line.get("occupancy") or 0)
    return total


def room_count(allocations: list[dict]) -> int:
    return sum(int(line.get("quantity") or 0) for line in allocations or [])
