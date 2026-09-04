from __future__ import annotations

from pymongo.errors import DuplicateKeyError, PyMongoError

from apps.bookings.constants import STATUS_LABELS
from apps.bookings.repositories import BookingRepository
from apps.customers.repositories import CustomerRepository
from apps.packages.validators import format_dates, parse_optional_object_id, parse_when
from apps.tours.repositories import TourRepository
from apps.tours.services import TourService
from core.constants import BookingStatus, Collections, DEFAULT_CURRENCY, DiscountType, PaymentStatus
from core.exceptions import BusinessRuleViolation, DatabaseUnavailableError, NotFoundError, ValidationError
from core.money import ZERO, to_decimal128, to_money
from core.numbering import next_number
from core.utils import full_name, parse_object_id, serialize_id, utcnow


def present_traveler(person: dict, *, index: int = 0, booking: dict | None = None) -> dict:
    name = full_name(person.get("first_name"), person.get("last_name")) or person.get("name") or "Traveler"
    dob = person.get("date_of_birth")
    return {
        "index": index,
        "booking_id": serialize_id((booking or {}).get("_id")),
        "booking_number": (booking or {}).get("booking_number") or "",
        "first_name": person.get("first_name") or "",
        "last_name": person.get("last_name") or "",
        "name": name,
        "passport": person.get("passport_number") or "",
        "passport_number": person.get("passport_number") or "",
        "nationality": person.get("nationality") or "",
        "date_of_birth": dob,
        "dob": dob.strftime("%d %b %Y") if hasattr(dob, "strftime") else (str(dob) if dob else ""),
        "room_type": person.get("room_type") or "",
        "room_number": person.get("room_number") or "",
        "hotel_reservation_id": serialize_id(person.get("hotel_reservation_id")),
        "type": person.get("type") or "",
    }


def _pricing_from(tour: dict, traveler_count: int) -> dict:
    unit = to_money(tour.get("selling_price_per_person"))
    subtotal = to_money(unit * traveler_count)
    return {
        "unit_price": to_decimal128(unit),
        "subtotal": to_decimal128(subtotal),
        "discount_type": DiscountType.NONE.value,
        "discount_value": to_decimal128(ZERO),
        "discount_amount": to_decimal128(ZERO),
        "taxable_amount": to_decimal128(subtotal),
        "tax_rate": to_decimal128(ZERO),
        "tax_amount": to_decimal128(ZERO),
        "total_amount": to_decimal128(subtotal),
    }


def present_booking(document: dict, *, customer: dict | None = None, tour: dict | None = None) -> dict:
    pricing = document.get("pricing") or {}
    travelers = document.get("travelers") or []
    count = int(document.get("travelers_count") or len(travelers) or 0)
    customer_name = "—"
    if customer:
        customer_name = full_name(customer.get("first_name"), customer.get("last_name")) or customer.get("email") or "—"
    tour_name = (tour or {}).get("name") or (tour or {}).get("tour_code") or ""
    start = (tour or {}).get("start_date")
    end = (tour or {}).get("end_date")
    status = document.get("booking_status") or BookingStatus.PENDING.value
    return {
        "id": str(document["_id"]),
        "number": document.get("booking_number") or "",
        "booking_number": document.get("booking_number") or "",
        "customer_id": serialize_id(document.get("customer_id")),
        "customer": customer_name,
        "tour_id": serialize_id(document.get("tour_id")),
        "tour": tour_name,
        "product": tour_name,
        "dates": format_dates(start, end),
        "travelers_count": count,
        "travelers": [
            present_traveler(person, index=index, booking=document)
            for index, person in enumerate(travelers)
            if isinstance(person, dict)
        ],
        "status": status,
        "status_label": STATUS_LABELS.get(status, status),
        "payment_status": document.get("payment_status") or PaymentStatus.UNPAID.value,
        "pay": document.get("payment_status") or PaymentStatus.UNPAID.value,
        "total": to_money(pricing.get("total_amount")),
        "currency": document.get("currency") or (tour or {}).get("currency") or DEFAULT_CURRENCY,
        "notes": document.get("notes") or "",
        "created_at": document.get("created_at"),
        "updated_at": document.get("updated_at"),
    }


def clean_travelers(raw) -> list[dict]:
    if raw in (None, ""):
        raise ValidationError("At least one traveler is required.")
    if not isinstance(raw, list):
        raise ValidationError("Travelers must be a list.")
    people = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValidationError(f"Traveler {index} is invalid.")
        first = (item.get("first_name") or "").strip()
        last = (item.get("last_name") or "").strip()
        if not first or not last:
            raise ValidationError(f"Traveler {index} needs a first and last name.")
        dob = item.get("date_of_birth")
        parsed_dob = parse_when(dob, field="date_of_birth", required=False) if dob not in (None, "") else None
        hotel_id = parse_optional_object_id(item.get("hotel_reservation_id"), field="hotel_reservation_id")
        people.append(
            {
                "first_name": first,
                "last_name": last,
                "passport_number": (item.get("passport_number") or item.get("passport") or "").strip() or None,
                "nationality": (item.get("nationality") or "").strip() or None,
                "date_of_birth": parsed_dob,
                "room_type": (item.get("room_type") or "").strip().upper() or None,
                "room_number": (item.get("room_number") or "").strip() or None,
                "hotel_reservation_id": hotel_id,
                "type": (item.get("type") or "").strip().upper() or None,
            }
        )
    if not people:
        raise ValidationError("At least one traveler is required.")
    return people


class BookingService:
    def __init__(
        self,
        repository: BookingRepository | None = None,
        tours: TourService | None = None,
        tour_repository: TourRepository | None = None,
        customer_repository: CustomerRepository | None = None,
    ):
        self.repository = repository or BookingRepository()
        self.tours = tours or TourService()
        self.tour_repository = tour_repository or TourRepository()
        self.customer_repository = customer_repository or CustomerRepository()

    def list_items(self, *, tour_id=None, customer_id=None, status: str | None = None) -> list[dict]:
        extra = {}
        if tour_id:
            extra["tour_id"] = parse_object_id(tour_id, field="tour_id")
        if customer_id:
            extra["customer_id"] = parse_object_id(customer_id, field="customer_id")
        if status:
            extra["booking_status"] = (status or "").strip().upper()
        return self.repository.list_bookings(extra or None)

    def list_presented(self, **filters) -> list[dict]:
        return [self._present(doc) for doc in self.list_items(**filters)]

    def get(self, booking_id) -> dict:
        try:
            document = self.repository.find_by_id(booking_id)
        except ValidationError as extra:
            raise NotFoundError("Booking not found.") from extra
        if not document:
            raise NotFoundError("Booking not found.")
        return document

    def get_presented(self, booking_id) -> dict:
        return self._present(self.get(booking_id))

    def create(self, data=None, user=None, *, actor_id=None, customer_id=None, tour_id=None, travelers=None, notes: str | None = None) -> dict:
        if isinstance(data, dict):
            actor_id = actor_id or (user or {}).get("id")
            return self._create_record(
                actor_id=actor_id,
                customer_id=data.get("customer_id"),
                tour_id=data.get("tour_id"),
                travelers=data.get("travelers"),
                notes=data.get("notes"),
                pricing=data.get("pricing"),
                travelers_count=data.get("travelers_count"),
            )
        return self._create_record(
            actor_id=actor_id,
            customer_id=customer_id,
            tour_id=tour_id,
            travelers=travelers,
            notes=notes,
        )

    def _create_record(
        self,
        *,
        actor_id,
        customer_id,
        tour_id,
        travelers,
        notes: str | None = None,
        pricing=None,
        travelers_count=None,
    ) -> dict:
        customer = self.repository.find_customer(customer_id)
        if not customer:
            raise ValidationError("Customer not found.")
        tour = self.tours.get(tour_id)
        people = clean_travelers(travelers)
        count = int(travelers_count or len(people) or 0)
        if travelers_count is not None and count != len(people):
            raise ValidationError("Travelers count does not match the number of travelers.")
        now = utcnow()
        document = {
            "booking_number": next_number(Collections.BOOKINGS),
            "customer_id": customer["_id"],
            "tour_id": tour["_id"],
            "travelers_count": len(people),
            "travelers": people,
            "booking_date": now,
            "pricing": self._pricing_document(tour, len(people), pricing),
            "booking_status": BookingStatus.PENDING.value,
            "payment_status": PaymentStatus.UNPAID.value,
            "notes": (notes or "").strip() or None,
            "created_by": parse_object_id(actor_id, field="created_by") if actor_id else None,
            "created_at": now,
            "updated_at": now,
        }
        try:
            result = self.repository.insert(document)
        except DuplicateKeyError as extra:
            raise ValidationError("A booking with this number already exists.") from extra
        except PyMongoError as extra:
            raise DatabaseUnavailableError("Could not save the booking.") from extra
        document["_id"] = result.inserted_id
        return self.get(document["_id"])

    def _pricing_document(self, tour: dict, traveler_count: int, pricing=None) -> dict:
        if not isinstance(pricing, dict):
            return _pricing_from(tour, traveler_count)
        unit = to_money(pricing.get("unit_price", tour.get("selling_price_per_person")))
        subtotal = to_money(pricing.get("subtotal", unit * traveler_count))
        discount_amount = to_money(pricing.get("discount_amount", ZERO))
        discount_value = to_money(pricing.get("discount_value", discount_amount))
        taxable_amount = to_money(pricing.get("taxable_amount", subtotal - discount_amount))
        tax_amount = to_money(pricing.get("tax_amount", ZERO))
        total_amount = to_money(pricing.get("total_amount", taxable_amount + tax_amount))
        return {
            "unit_price": to_decimal128(unit),
            "subtotal": to_decimal128(subtotal),
            "discount_type": pricing.get("discount_type") or DiscountType.NONE.value,
            "discount_value": to_decimal128(discount_value),
            "discount_amount": to_decimal128(discount_amount),
            "discount_reason": pricing.get("discount_reason"),
            "discount_applied_by": pricing.get("discount_applied_by"),
            "taxable_amount": to_decimal128(taxable_amount),
            "tax_id": pricing.get("tax_id"),
            "tax_rate": to_decimal128(pricing.get("tax_rate", ZERO)),
            "tax_amount": to_decimal128(tax_amount),
            "total_amount": to_decimal128(total_amount),
        }

    def confirm(self, booking_id, user=None, *, actor_id=None) -> dict:
        document = self.get(booking_id)
        status = document.get("booking_status")
        if status == BookingStatus.CONFIRMED.value:
            return document
        if status == BookingStatus.CANCELLED.value:
            raise BusinessRuleViolation("A cancelled booking cannot be confirmed.")
        if status == BookingStatus.COMPLETED.value:
            raise BusinessRuleViolation("A completed booking is already confirmed.")
        tour = self.tours.get(document["tour_id"])
        count = int(document.get("travelers_count") or len(document.get("travelers") or []))
        booked = int(tour.get("booked_seats") or 0)
        capacity = int(tour.get("capacity") or 0)
        if booked + count > capacity:
            raise BusinessRuleViolation(
                f"Not enough tour seats. {booked} of {capacity} are already booked; this booking needs {count}."
            )
        self.tours.adjust_booked_seats(tour["_id"], count)
        try:
            self.repository.update(
                document["_id"],
                {"booking_status": BookingStatus.CONFIRMED.value, "updated_at": utcnow()},
            )
        except PyMongoError as extra:
            self.tours.adjust_booked_seats(tour["_id"], -count)
            raise DatabaseUnavailableError("Could not confirm the booking.") from extra
        return self.get(document["_id"])

    def cancel(self, booking_id, user=None, *, actor_id=None) -> dict:
        document = self.get(booking_id)
        status = document.get("booking_status")
        if status == BookingStatus.CANCELLED.value:
            return document
        if status == BookingStatus.COMPLETED.value:
            raise BusinessRuleViolation("A completed booking cannot be cancelled here.")
        if status == BookingStatus.CONFIRMED.value:
            count = int(document.get("travelers_count") or len(document.get("travelers") or []))
            self.tours.adjust_booked_seats(document["tour_id"], -count)
        try:
            self.repository.update(
                document["_id"],
                {"booking_status": BookingStatus.CANCELLED.value, "updated_at": utcnow()},
            )
        except PyMongoError as extra:
            raise DatabaseUnavailableError("Could not cancel the booking.") from extra
        return self.get(document["_id"])

    def assign_rooms(self, booking_id, assignments: list[dict], *, actor_id, tour_id=None) -> dict:
        document = self.get(booking_id)
        if tour_id and str(document.get("tour_id")) != str(tour_id):
            raise ValidationError("Booking does not belong to this tour.")
        travelers = list(document.get("travelers") or [])
        for item in assignments:
            index = item.get("traveler_index", item.get("index"))
            try:
                index = int(index)
            except (TypeError, ValueError) as extra:
                raise ValidationError("Invalid traveler index.") from extra
            if index < 0 or index >= len(travelers):
                raise ValidationError("Traveler index is out of range.")
            person = dict(travelers[index])
            if "room_number" in item:
                person["room_number"] = (item.get("room_number") or "").strip() or None
            if "room_type" in item:
                person["room_type"] = (item.get("room_type") or "").strip().upper() or None
            if "hotel_reservation_id" in item:
                person["hotel_reservation_id"] = parse_optional_object_id(
                    item.get("hotel_reservation_id"), field="hotel_reservation_id"
                )
            travelers[index] = person
        try:
            self.repository.update(document["_id"], {"travelers": travelers, "updated_at": utcnow()})
        except PyMongoError as extra:
            raise DatabaseUnavailableError("Could not save room assignments.") from extra
        return self.get(document["_id"])

    def _present(self, document: dict) -> dict:
        customer = None
        tour = None
        if document.get("customer_id"):
            customer = self.repository.find_customer(document["customer_id"])
        if document.get("tour_id"):
            tour = self.repository.find_tour(document["tour_id"])
        return present_booking(document, customer=customer, tour=tour)
