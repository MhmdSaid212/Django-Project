"""
Money helpers.

Decision:
- Python code always uses decimal.Decimal for money math.
- MongoDB stores money as bson.Decimal128.
- Repositories convert at the database boundary.
- Never use float for financial values (0.1 + 0.2 != 0.3).
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Any

from bson.decimal128 import Decimal128

TWOPLACE = Decimal("0.01")
ZERO = Decimal("0.00")


def to_decimal(value: Any) -> Decimal:
    """Convert Decimal128 / str / int / Decimal to Decimal. Reject float."""
    if value is None:
        return ZERO
    if isinstance(value, float):
        raise TypeError(
            "Refusing to convert float to money. Pass Decimal, str, int, or Decimal128."
        )
    if isinstance(value, Decimal128):
        return value.to_decimal()
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Cannot convert {value!r} to Decimal") from exc


def to_money(value: Any) -> Decimal:
    """Quantize to 2 decimal places using banker's-unfriendly ROUND_HALF_UP."""
    return to_decimal(value).quantize(TWOPLACE, rounding=ROUND_HALF_UP)


def to_decimal128(value: Any) -> Decimal128:
    """Convert a money value to BSON Decimal128 for MongoDB inserts/updates."""
    return Decimal128(str(to_money(value)))


def money_dict(document: dict, *field_names: str) -> dict:
    """
    Return a copy of document with named fields converted Decimal128 -> Decimal.
    Use when reading documents in services.
    """
    result = dict(document)
    for name in field_names:
        if name in result and result[name] is not None:
            result[name] = to_decimal(result[name])
    return result
