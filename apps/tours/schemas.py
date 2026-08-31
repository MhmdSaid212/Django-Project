"""
Tour document contract. NOT a Django model.

OWNER: Dev 2 — Travel Products & Suppliers
Collection: tours

A tour is a dated, bookable departure. It MAY reference a package
(template) via optional package_id. A tour can also be a standalone product.
Clients book tours only — never packages.

Available seats MUST be derived:
    available_seats = capacity - booked_seats
Never store available_seats as the source of truth.

When package_id is set, copy selling price / inclusions / planned services from
the package, then set start_date, end_date, and capacity for this departure.
When package_id is null, the tour is a standalone sellable product.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

from bson import ObjectId

from core.constants import TourStatus
from core.schemas import Destination, SupplierServiceLine


def available_seats(capacity: int, booked_seats: int) -> int:
    return max(capacity - booked_seats, 0)


@dataclass
class TourDocument:
    tour_code: str
    name: str
    destination: Destination
    description: str
    start_date: datetime
    end_date: datetime
    capacity: int
    booked_seats: int
    selling_price_per_person: Decimal
    currency: str
    created_by: ObjectId
    created_at: datetime
    updated_at: datetime
    package_id: Optional[ObjectId] = None
    updated_by: Optional[ObjectId] = None
    status: str = TourStatus.DRAFT.value
    services: list[SupplierServiceLine] = field(default_factory=list)
    included_services: list[str] = field(default_factory=list)
    excluded_services: list[str] = field(default_factory=list)
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[ObjectId] = None
    _id: Optional[ObjectId] = None

    @property
    def available_seats(self) -> int:
        return available_seats(self.capacity, self.booked_seats)
