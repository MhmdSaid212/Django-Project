from __future__ import annotations

from datetime import date, datetime

from pymongo.errors import DuplicateKeyError, PyMongoError

from apps.audit.constants import AuditAction
from apps.audit.services import safe_audit
from apps.packages.validators import format_dates, parse_when
from apps.supplier_reservations.constants import (
    DEFAULT_OCCUPANCY,
    ROOM_TYPE_LABELS,
    SERVICE_TYPE_LABELS,
    STATUS_LABELS,
)
from apps.supplier_reservations.repositories import SupplierReservationRepository
from apps.supplier_reservations.validators import (
    bed_capacity,
    clean_room_allocations,
    room_count,
    validate_service_type,
    validate_status,
)
from core.constants import (
    BookingStatus,
    Collections,
    SupplierReservationStatus,
    SupplierType,
)
from core.exceptions import BusinessRuleViolation, DatabaseUnavailableError, NotFoundError, ValidationError
from core.numbering import next_number
from core.utils import full_name, parse_object_id, serialize_id, utcnow


def _blank(value) -> str | None:
    text = (str(value).strip() if value is not None else "") or None
    return text


def _as_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None


def present_allocation(line: dict) -> dict:
    room_type = line.get("room_type") or ""
    quantity = int(line.get("quantity") or 0)
    occupancy = int(line.get("occupancy") or DEFAULT_OCCUPANCY.get(room_type, 1))
    return {
        "room_type": room_type,
        "type_label": ROOM_TYPE_LABELS.get(room_type, room_type),
        "quantity": quantity,
        "occupancy": occupancy,
        "beds": quantity * occupancy,
    }


def present_reservation(document: dict, *, supplier: dict | None = None, tour: dict | None = None) -> dict:
    allocations = [present_allocation(line) for line in document.get("room_allocations") or []]
    status = document.get("status") or SupplierReservationStatus.REQUESTED.value
    service_type = document.get("service_type") or ""
    start = document.get("start_date")
    end = document.get("end_date")
    release = document.get("release_date")
    today = utcnow().date()
    release_day = _as_date(release)
    start_day = _as_date(start)
    release_days = (release_day - today).days if release_day else None
    allocation_label = ", ".join(f"{line['quantity']} {line['type_label']}" for line in allocations) or "—"
    created = document.get("created_at")
    return {
        "id": str(document["_id"]),
        "number": document.get("reservation_number") or "",
        "reservation_number": document.get("reservation_number") or "",
        "tour_id": serialize_id(document.get("tour_id")),
        "tour": (tour or {}).get("name") or (tour or {}).get("tour_code") or "",
        "tour_code": (tour or {}).get("tour_code") or "",
        "supplier_id": serialize_id(document.get("supplier_id")),
        "supplier": (supplier or {}).get("name") or "—",
        "supplier_email": (supplier or {}).get("email") or "",
        "supplier_phone": (supplier or {}).get("phone") or "",
        "service_type": service_type,
        "service_label": SERVICE_TYPE_LABELS.get(service_type, service_type),
        "is_hotel": service_type == SupplierType.HOTEL.value,
        "status": status,
        "status_label": STATUS_LABELS.get(status, status),
        "confirmation_number": document.get("confirmation_number") or "",
        "dates": format_dates(start, end),
        "start_date": start,
        "end_date": end,
        "start_label": start.strftime("%d %b %Y") if hasattr(start, "strftime") else (str(start) if start else ""),
        "end_label": end.strftime("%d %b %Y") if hasattr(end, "strftime") else (str(end) if end else ""),
        "release_date": release,
        "release": release.strftime("%d %b %Y") if hasattr(release, "strftime") else (str(release) if release else ""),
        "release_days": release_days,
        "release_approaching": release_days is not None and 0 <= release_days <= 7,
        "release_passed": release_days is not None and release_days < 0,
        "room_allocations": allocations,
        "allocation_label": allocation_label,
        "room_count": room_count(document.get("room_allocations") or []),
        "bed_capacity": bed_capacity(document.get("room_allocations") or []),
        "quantity": document.get("quantity"),
        "notes": document.get("notes") or "",
        "is_cancelled": status == SupplierReservationStatus.CANCELLED.value,
        "is_confirmed": status == SupplierReservationStatus.CONFIRMED.value,
        "is_requested": status == SupplierReservationStatus.REQUESTED.value,
        "is_upcoming": bool(start_day and start_day >= today and status != SupplierReservationStatus.CANCELLED.value),
        "created_at": created,
        "created_label": created.strftime("%d %b %Y, %H:%M") if hasattr(created, "strftime") else (str(created) if created else ""),
        "updated_at": document.get("updated_at"),
    }


class SupplierReservationService:
    def __init__(self, repository: SupplierReservationRepository | None = None):
        self.repository = repository or SupplierReservationRepository()

    def list_items(self, *, tour_id=None, supplier_id=None, status: str | None = None) -> list[dict]:
        extra = {}
        if tour_id:
            extra["tour_id"] = parse_object_id(tour_id, field="tour_id")
        if supplier_id:
            extra["supplier_id"] = parse_object_id(supplier_id, field="supplier_id")
        if status:
            extra["status"] = validate_status(status)
        return self.repository.list_reservations(extra or None)

    def list_presented(self, **filters) -> list[dict]:
        return [self._present(doc) for doc in self.list_items(**filters)]

    def list_for_tour(self, tour_id) -> list[dict]:
        tour = self._require_tour(tour_id)
        return [self._present(doc, tour=tour) for doc in self.repository.list_for_tour(tour["_id"])]

    def get(self, reservation_id) -> dict:
        try:
            document = self.repository.find_by_id(reservation_id)
        except ValidationError as extra:
            raise NotFoundError("Supplier reservation not found.") from extra
        if not document:
            raise NotFoundError("Supplier reservation not found.")
        return document

    def get_presented(self, reservation_id) -> dict:
        return self._present(self.get(reservation_id))

    def create(
        self,
        *,
        actor_id,
        tour_id,
        supplier_id,
        start_date=None,
        end_date=None,
        status: str | None = None,
        confirmation_number: str | None = None,
        release_date=None,
        room_allocations=None,
        quantity=None,
        notes: str | None = None,
        service_type: str | None = None,
    ) -> dict:
        tour = self._require_tour(tour_id)
        supplier = self._require_supplier(supplier_id)
        service_type = validate_service_type(service_type or supplier.get("supplier_type") or "")
        start = parse_when(start_date, field="start_date") if start_date not in (None, "") else tour.get("start_date")
        end = parse_when(end_date, field="end_date") if end_date not in (None, "") else tour.get("end_date")
        if start is None or end is None:
            raise ValidationError("Start and end dates are required.")
        if end < start:
            raise ValidationError("End date cannot be before start date.")
        release = parse_when(release_date, field="release_date", required=False) if release_date not in (None, "") else None

        allocations = clean_room_allocations(room_allocations)
        if service_type == SupplierType.HOTEL.value and not allocations:
            raise ValidationError("Hotel reservations need at least one room type allocation.")
        if service_type != SupplierType.HOTEL.value:
            allocations = []

        qty = None
        if quantity not in (None, ""):
            qty = int(quantity)
            if qty < 1:
                raise ValidationError("Quantity must be at least 1.")

        next_status = validate_status(status or SupplierReservationStatus.REQUESTED.value)
        confirmation = _blank(confirmation_number)
        if next_status == SupplierReservationStatus.CONFIRMED.value and not confirmation:
            raise ValidationError("A confirmation number is required once the supplier confirms.")
        if next_status == SupplierReservationStatus.CANCELLED.value:
            raise ValidationError("Create the reservation first, then cancel it.")

        now = utcnow()
        document = {
            "reservation_number": next_number(Collections.SUPPLIER_RESERVATIONS),
            "tour_id": tour["_id"],
            "supplier_id": supplier["_id"],
            "service_type": service_type,
            "start_date": start,
            "end_date": end,
            "status": next_status,
            "confirmation_number": confirmation,
            "release_date": release,
            "room_allocations": allocations,
            "quantity": qty,
            "notes": _blank(notes),
            "recorded_by": parse_object_id(actor_id, field="recorded_by"),
            "created_at": now,
            "updated_at": now,
        }
        try:
            result = self.repository.insert(document)
        except DuplicateKeyError as extra:
            raise ValidationError("A supplier reservation with this number already exists.") from extra
        except PyMongoError as extra:
            raise DatabaseUnavailableError("Could not save the supplier reservation.") from extra
        document["_id"] = result.inserted_id
        saved = self.get(document["_id"])
        safe_audit(
            actor_id=actor_id,
            action=AuditAction.CREATED.value,
            entity_type="supplier_reservations",
            entity_id=saved["_id"],
            description=f"Recorded supplier reservation {saved.get('reservation_number')}.",
        )
        return saved

    def update(self, reservation_id, *, actor_id=None, **fields) -> dict:
        document = self.get(reservation_id)
        if document.get("status") == SupplierReservationStatus.CANCELLED.value:
            raise BusinessRuleViolation("A cancelled reservation cannot be edited.")
        updates = {}
        if "start_date" in fields and fields["start_date"] not in (None, ""):
            updates["start_date"] = parse_when(fields["start_date"], field="start_date")
        if "end_date" in fields and fields["end_date"] not in (None, ""):
            updates["end_date"] = parse_when(fields["end_date"], field="end_date")
        start = updates.get("start_date", document.get("start_date"))
        end = updates.get("end_date", document.get("end_date"))
        if start and end and end < start:
            raise ValidationError("End date cannot be before start date.")
        if "release_date" in fields:
            updates["release_date"] = (
                parse_when(fields["release_date"], field="release_date", required=False)
                if fields["release_date"] not in (None, "")
                else None
            )
        if "notes" in fields:
            updates["notes"] = _blank(fields["notes"])
        if "confirmation_number" in fields:
            updates["confirmation_number"] = _blank(fields["confirmation_number"])
        if "quantity" in fields:
            if fields["quantity"] in (None, ""):
                updates["quantity"] = None
            else:
                qty = int(fields["quantity"])
                if qty < 1:
                    raise ValidationError("Quantity must be at least 1.")
                updates["quantity"] = qty
        if "room_allocations" in fields:
            allocations = clean_room_allocations(fields["room_allocations"])
            if document.get("service_type") == SupplierType.HOTEL.value and not allocations:
                raise ValidationError("Hotel reservations need at least one room type allocation.")
            updates["room_allocations"] = allocations
        if "status" in fields and fields["status"] is not None:
            updates["status"] = self._next_status(document, fields["status"], updates)
        if not updates:
            return document
        updates["updated_at"] = utcnow()
        try:
            self.repository.update(document["_id"], updates)
        except PyMongoError as extra:
            raise DatabaseUnavailableError("Could not update the supplier reservation.") from extra
        saved = self.get(document["_id"])
        safe_audit(
            actor_id=actor_id or document.get("recorded_by"),
            action=AuditAction.UPDATED.value,
            entity_type="supplier_reservations",
            entity_id=saved["_id"],
            description=f"Updated supplier reservation {saved.get('reservation_number')}.",
        )
        return saved

    def confirm(self, reservation_id, *, actor_id, confirmation_number: str, notes: str | None = None) -> dict:
        extra = {}
        if notes not in (None, ""):
            document = self.get(reservation_id)
            existing = (document.get("notes") or "").strip()
            extra["notes"] = f"{existing}\n{notes.strip()}".strip() if existing else notes.strip()
        return self.update(
            reservation_id,
            actor_id=actor_id,
            status=SupplierReservationStatus.CONFIRMED.value,
            confirmation_number=confirmation_number,
            **extra,
        )

    def cancel(self, reservation_id, *, actor_id) -> dict:
        return self.update(reservation_id, actor_id=actor_id, status=SupplierReservationStatus.CANCELLED.value)

    def accommodation_snapshot(self, tour_id) -> dict:
        tour = self._require_tour(tour_id)
        reservations = [self._present(doc, tour=tour) for doc in self.repository.list_for_tour(tour["_id"])]
        hotels = [
            row
            for row in reservations
            if row["is_hotel"] and row["status"] != SupplierReservationStatus.CANCELLED.value
        ]
        travelers = self._confirmed_travelers(tour["_id"])
        confirmed_count = len(travelers)
        beds = sum(row["bed_capacity"] for row in hotels)
        rooms = sum(row["room_count"] for row in hotels)
        shortage = max(confirmed_count - beds, 0)
        unused_beds = max(beds - confirmed_count, 0)
        unassigned = [person for person in travelers if not person.get("room_number")]
        assignment_warnings = self._assignment_warnings(hotels, travelers)
        today = utcnow().date()
        release_notes = []
        for hotel in hotels:
            release = _as_date(hotel.get("release_date"))
            if release and release <= today and unused_beds:
                release_notes.append(
                    f"{hotel['supplier']} release date {hotel['release']} — {unused_beds} bed(s) currently unused."
                )
        warnings = []
        if shortage:
            warnings.append(f"Accommodation allocation is insufficient for {shortage} traveler(s).")
        if unassigned and confirmed_count:
            warnings.append(f"{len(unassigned)} confirmed traveler(s) have no room assignment.")
        warnings.extend(assignment_warnings)
        warnings.extend(release_notes)
        if shortage:
            capacity_state = "SHORTAGE"
            capacity_label = "Shortage"
        elif unused_beds:
            capacity_state = "UNUSED"
            capacity_label = "Unused capacity"
        elif beds:
            capacity_state = "OK"
            capacity_label = "Capacity OK"
        else:
            capacity_state = "NONE"
            capacity_label = "No hotel allocation"
        difference = beds - confirmed_count
        return {
            "tour_id": str(tour["_id"]),
            "tour_name": tour.get("name") or tour.get("tour_code") or "Tour",
            "tour_code": tour.get("tour_code") or "",
            "dates": format_dates(tour.get("start_date"), tour.get("end_date")),
            "confirmed_travelers": confirmed_count,
            "bed_capacity": beds,
            "room_count": rooms,
            "shortage_travelers": shortage,
            "unused_beds": unused_beds,
            "difference": difference,
            "capacity_state": capacity_state,
            "capacity_label": capacity_label,
            "unassigned_count": len(unassigned),
            "hotels": hotels,
            "reservations": reservations,
            "warnings": warnings,
            "ok": not shortage and not assignment_warnings,
        }

    def rooming_list(self, tour_id, *, reservation_id=None) -> dict:
        tour = self._require_tour(tour_id)
        snapshot = self.accommodation_snapshot(tour["_id"])
        reservation = None
        if reservation_id:
            reservation = self.get_presented(reservation_id)
            if reservation["tour_id"] != str(tour["_id"]):
                raise ValidationError("Reservation does not belong to this tour.")
        travelers = self._confirmed_travelers(tour["_id"])
        if reservation:
            travelers = [
                person
                for person in travelers
                if person.get("hotel_reservation_id") in {None, "", reservation["id"]}
                or person.get("hotel_reservation_id") == reservation["id"]
            ]
        rooms = self._group_rooms(travelers, reservation_id=reservation["id"] if reservation else None)
        names = {hotel["id"]: hotel["supplier"] for hotel in snapshot.get("hotels") or []}
        grouped: dict[str, dict] = {}
        order: list[str] = []
        for room in rooms:
            hotel_id = room.get("hotel_reservation_id") or ""
            room["hotel_name"] = names.get(hotel_id, "")
            if hotel_id not in grouped:
                grouped[hotel_id] = {
                    "id": hotel_id,
                    "supplier": room["hotel_name"] or names.get(hotel_id) or "Hotel",
                    "rooms": [],
                }
                order.append(hotel_id)
            grouped[hotel_id]["rooms"].append(room)
        unassigned = [person for person in travelers if not (person.get("room_number") or "").strip()]
        assigned_count = len(travelers) - len(unassigned)
        return {
            "tour": {
                "id": str(tour["_id"]),
                "name": tour.get("name") or tour.get("tour_code") or "Tour",
                "code": tour.get("tour_code") or "",
                "dates": format_dates(tour.get("start_date"), tour.get("end_date")),
            },
            "reservation": reservation,
            "rooms": rooms,
            "hotels_grouped": [grouped[key] for key in order],
            "unassigned": unassigned,
            "assigned_count": assigned_count,
            "unassigned_count": len(unassigned),
            "travelers": travelers,
            "snapshot": snapshot,
        }

    def assign_rooms(self, tour_id, assignments: list[dict], *, actor_id) -> dict:
        from apps.bookings.services import BookingService

        tour = self._require_tour(tour_id)
        bookings = BookingService()
        grouped: dict[str, list[dict]] = {}
        for item in assignments or []:
            if not isinstance(item, dict):
                continue
            booking_id = item.get("booking_id")
            if not booking_id:
                continue
            grouped.setdefault(str(booking_id), []).append(item)
        for booking_id, rows in grouped.items():
            bookings.assign_rooms(booking_id, rows, actor_id=actor_id, tour_id=tour["_id"])
        return self.rooming_list(tour["_id"])

    def list_supplier_options(self) -> list[tuple[str, str]]:
        return [
            (str(doc["_id"]), doc.get("name") or doc.get("supplier_number") or "Supplier")
            for doc in self.repository.list_suppliers()
        ]

    def match_planned(self, services: list[dict], reservations: list[dict]) -> list[dict]:
        by_supplier: dict[str, list[dict]] = {}
        for row in reservations or []:
            if row.get("is_cancelled"):
                continue
            by_supplier.setdefault(row.get("supplier_id") or "", []).append(row)
        matched = []
        for line in services or []:
            linked = by_supplier.get(line.get("supplier_id") or "") or []
            matched.append(
                {
                    "title": line.get("title") or line.get("description") or "Service",
                    "supplier": line.get("supplier") or "—",
                    "supplier_id": line.get("supplier_id"),
                    "type_label": line.get("type_label") or line.get("supplier_type") or "",
                    "estimated_cost": line.get("estimated_cost") or line.get("est"),
                    "reservations": linked,
                    "has_reservation": bool(linked),
                }
            )
        return matched

    def ops_desk(self) -> dict:
        rows = self.list_presented()
        live = [row for row in rows if not row["is_cancelled"]]
        requested = [row for row in live if row["is_requested"]]
        confirmed = [row for row in live if row["is_confirmed"]]
        upcoming = [row for row in live if row.get("is_upcoming")]
        release_watch = [row for row in live if row.get("release_approaching") or row.get("release_passed")]
        shortages = []
        seen = set()
        for row in live:
            tour_id = row.get("tour_id")
            if not tour_id or tour_id in seen or not row["is_hotel"]:
                continue
            seen.add(tour_id)
            snapshot = self.accommodation_snapshot(tour_id)
            if snapshot["shortage_travelers"]:
                shortages.append(snapshot)
        return {
            "requested": len(requested),
            "confirmed": len(confirmed),
            "upcoming": len(upcoming),
            "shortages": shortages,
            "shortage_count": len(shortages),
            "release_watch": release_watch,
            "awaiting": requested,
            "reservations": rows,
        }

    def related_expenses(self, *, supplier_id, tour_id) -> list[dict]:
        from apps.expenses.services import ExpenseService

        rows = []
        for expense in ExpenseService().list_presented(supplier_id=supplier_id):
            if tour_id and expense.get("tour_id") and expense.get("tour_id") != str(tour_id):
                continue
            rows.append(expense)
        return rows

    def _next_status(self, document: dict, requested, updates: dict) -> str:
        status = validate_status(requested)
        current = document.get("status")
        if current == status:
            return status
        if current == SupplierReservationStatus.CANCELLED.value:
            raise BusinessRuleViolation("A cancelled reservation cannot change status.")
        if status == SupplierReservationStatus.CONFIRMED.value:
            confirmation = updates.get("confirmation_number", document.get("confirmation_number"))
            if not confirmation:
                raise ValidationError("A confirmation number is required once the supplier confirms.")
        if status == SupplierReservationStatus.REQUESTED.value and current == SupplierReservationStatus.CONFIRMED.value:
            return status
        return status

    def _require_tour(self, tour_id) -> dict:
        try:
            tour = self.repository.find_tour(tour_id)
        except ValidationError as extra:
            raise NotFoundError("Tour not found.") from extra
        if not tour:
            raise NotFoundError("Tour not found.")
        return tour

    def _require_supplier(self, supplier_id) -> dict:
        try:
            supplier = self.repository.find_supplier(supplier_id)
        except ValidationError as extra:
            raise ValidationError("Supplier not found.") from extra
        if not supplier:
            raise ValidationError("Supplier not found.")
        return supplier

    def _present(self, document: dict, *, tour=None, supplier=None) -> dict:
        if supplier is None and document.get("supplier_id"):
            supplier = self.repository.find_supplier(document["supplier_id"])
        if tour is None and document.get("tour_id"):
            tour = self.repository.find_tour(document["tour_id"])
        return present_reservation(document, supplier=supplier, tour=tour)

    def _confirmed_travelers(self, tour_id) -> list[dict]:
        from apps.bookings.services import present_traveler

        travelers = []
        query = {"tour_id": tour_id, "booking_status": BookingStatus.CONFIRMED.value, "is_deleted": {"$ne": True}}
        for booking in self.repository.bookings.find(query):
            for index, person in enumerate(booking.get("travelers") or []):
                if not isinstance(person, dict):
                    continue
                row = present_traveler(person, index=index, booking=booking)
                travelers.append(row)
        return travelers

    def _group_rooms(self, travelers: list[dict], *, reservation_id=None) -> list[dict]:
        grouped: dict[tuple, dict] = {}
        for person in travelers:
            number = (person.get("room_number") or "").strip()
            if not number:
                continue
            hotel_id = person.get("hotel_reservation_id") or ""
            if reservation_id and hotel_id and hotel_id != reservation_id:
                continue
            key = (hotel_id, number, person.get("room_type") or "")
            bucket = grouped.setdefault(
                key,
                {
                    "room_number": number,
                    "room_type": person.get("room_type") or "",
                    "type_label": ROOM_TYPE_LABELS.get(person.get("room_type") or "", person.get("room_type") or "Room"),
                    "hotel_reservation_id": hotel_id,
                    "guests": [],
                },
            )
            bucket["guests"].append(person)
        rooms = list(grouped.values())
        rooms.sort(key=lambda row: (row["room_number"], row["room_type"]))
        return rooms

    def _assignment_warnings(self, hotels: list[dict], travelers: list[dict]) -> list[str]:
        warnings = []
        by_hotel: dict[str, dict[str, set[str]]] = {}
        occupancy_used: dict[str, dict[str, int]] = {}
        for person in travelers:
            hotel_id = person.get("hotel_reservation_id")
            room_type = person.get("room_type")
            room_number = (person.get("room_number") or "").strip()
            if not hotel_id or not room_type or not room_number:
                continue
            by_hotel.setdefault(hotel_id, {}).setdefault(room_type, set()).add(room_number)
            occupancy_used.setdefault(hotel_id, {}).setdefault(room_type, 0)
            occupancy_used[hotel_id][room_type] += 1
        hotels_by_id = {row["id"]: row for row in hotels}
        for hotel in hotels:
            allocated = {line["room_type"]: line for line in hotel.get("room_allocations") or []}
            used_rooms = by_hotel.get(hotel["id"]) or {}
            used_people = occupancy_used.get(hotel["id"]) or {}
            for room_type, line in allocated.items():
                assigned_rooms = len(used_rooms.get(room_type, set()))
                if assigned_rooms > line["quantity"]:
                    warnings.append(
                        f"{hotel['supplier']}: {assigned_rooms} {line['type_label'].lower()} rooms assigned, "
                        f"only {line['quantity']} allocated."
                    )
                people = used_people.get(room_type, 0)
                if people > line["beds"]:
                    warnings.append(
                        f"{hotel['supplier']}: {people} travelers assigned to {line['type_label'].lower()} rooms, "
                        f"which sleep {line['beds']}."
                    )
        for hotel_id, types in by_hotel.items():
            if hotel_id and hotel_id not in hotels_by_id:
                warnings.append("Travelers are assigned to a hotel reservation that is missing or cancelled.")
        return warnings
