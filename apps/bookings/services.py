from bson import ObjectId
import json
from apps.customers.repositories import CustomerRepository
from apps.bookings.repositories import BookingRepository
from apps.tours.repositories import TourRepository
from apps.tours.schemas import available_seats
from decimal import Decimal
from core.money import to_money, to_decimal128
from core.constants import (BookingStatus,Collections,PaymentStatus)
from core.exceptions import NotFoundError, TourOpsError, ValidationError
from core.numbering import next_number
from core.utils import utcnow
from core.utils import parse_object_id


class BookingService:
    def __init__(
      self,
       repository: BookingRepository | None = None,
       tour_repository: TourRepository | None = None,
       customer_repository: CustomerRepository | None = None,
):
       self.repository = repository or BookingRepository()
       self.tour_repository = tour_repository or TourRepository()
       self.customer_repository = customer_repository or CustomerRepository()

    def list_items(
        self,
        status: str | None = None,
        customer_id: str | None = None,
        tour_id: str | None = None,
        include_deleted: bool = False,
    ):
        return self.repository.find_all(
            status=status,
            customer_id=customer_id,
            tour_id=tour_id,
            include_deleted=include_deleted,
        )

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
    def get_item(self, booking_id: str) -> dict:
     booking = self.repository.find_by_id(booking_id)

     if not booking:
        raise NotFoundError("Booking not found.")

     return booking



    def _validate_pricing(self, pricing: dict, travelers_count: int) -> dict:
        if not isinstance(pricing, dict):
            raise ValidationError("pricing must be an object.")

        try:
            unit_price = to_money(pricing["unit_price"])
            subtotal = to_money(pricing["subtotal"])
            discount_type = pricing["discount_type"]
            discount_value = to_money(pricing["discount_value"])
            discount_amount = to_money(pricing["discount_amount"])
            taxable_amount = to_money(pricing["taxable_amount"])
            tax_rate = Decimal(str(pricing["tax_rate"]))
            tax_amount = to_money(pricing["tax_amount"])
            total_amount = to_money(pricing["total_amount"])
        except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
            raise ValidationError("Invalid pricing data.") from exc

        if (
            unit_price < 0
            or subtotal < 0
            or discount_value < 0
            or discount_amount < 0
            or taxable_amount < 0
            or tax_rate < 0
            or tax_amount < 0
            or total_amount < 0
        ):
            raise ValidationError("Pricing values cannot be negative.")

        expected_subtotal = to_money(unit_price * travelers_count)

        if subtotal != expected_subtotal:
            raise ValidationError("Invalid subtotal.")

        if discount_type == "NONE":
            if discount_value != Decimal("0.00"):
                raise ValidationError(
                    "Discount value must be zero when discount type is NONE."
                )

            expected_discount = Decimal("0.00")

        elif discount_type == "PERCENTAGE":
            if discount_value > Decimal("100.00"):
                raise ValidationError(
                    "Percentage discount cannot exceed 100%."
                )

            expected_discount = to_money(
                subtotal * discount_value / Decimal("100")
            )

        elif discount_type == "FIXED":
            expected_discount = discount_value

        else:
            raise ValidationError("Invalid discount type.")

        if expected_discount > subtotal:
            raise ValidationError("Discount cannot exceed subtotal.")

        if discount_amount != expected_discount:
            raise ValidationError("Invalid discount amount.")

        expected_taxable = to_money(
            subtotal - discount_amount
        )

        if taxable_amount != expected_taxable:
            raise ValidationError("Invalid taxable amount.")

        expected_tax = to_money(
            taxable_amount * tax_rate / Decimal("100")
        )

        if tax_amount != expected_tax:
            raise ValidationError("Invalid tax amount.")

        expected_total = to_money(
            taxable_amount + tax_amount
        )

        if total_amount != expected_total:
            raise ValidationError("Invalid total amount.")

        return {
            "unit_price": unit_price,
            "subtotal": subtotal,
            "discount_type": discount_type,
            "discount_value": discount_value,
            "discount_amount": discount_amount,
            "discount_reason": pricing.get("discount_reason"),
            "discount_applied_by": pricing.get("discount_applied_by"),
            "taxable_amount": taxable_amount,
            "tax_id": pricing.get("tax_id"),
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
        }

    def update(self, booking_id: str, data: dict, user=None) -> dict:
        booking = self.get_item(booking_id)

        if booking.get("booking_status") != BookingStatus.PENDING.value:
            raise ValidationError(
                "Only pending bookings can be updated."
            )

        allowed_fields = {
            "travelers",
            "travelers_count",
            "pricing",
            "notes",
        }

        invalid_fields = set(data.keys()) - allowed_fields

        if invalid_fields:
            raise ValidationError(
                f"These fields cannot be updated: {', '.join(sorted(invalid_fields))}."
            )

        if not data:
            raise ValidationError("No fields provided for update.")

        updates = {}
        seat_difference = 0

        final_count = data.get(
            "travelers_count",
            booking["travelers_count"],
        )

        if "pricing" in data:
            validated_pricing = self._validate_pricing(
                data["pricing"],
                final_count,
            )

            updates["pricing"] = {
                "unit_price": to_decimal128(validated_pricing["unit_price"]),
                "subtotal": to_decimal128(validated_pricing["subtotal"]),
                "discount_type": validated_pricing["discount_type"],
                "discount_value": to_decimal128(validated_pricing["discount_value"]),
                "discount_amount": to_decimal128(validated_pricing["discount_amount"]),
                "discount_reason": validated_pricing["discount_reason"],
                "discount_applied_by": validated_pricing["discount_applied_by"],
                "taxable_amount": to_decimal128(validated_pricing["taxable_amount"]),
                "tax_id": validated_pricing["tax_id"],
                "tax_rate": to_decimal128(validated_pricing["tax_rate"]),
                "tax_amount": to_decimal128(validated_pricing["tax_amount"]),
                "total_amount": to_decimal128(validated_pricing["total_amount"]),
            }

        if "travelers_count" in data:
            travelers_count = data["travelers_count"]

            if (
                isinstance(travelers_count, bool)
                or not isinstance(travelers_count, int)
                or travelers_count <= 0
            ):
                raise ValidationError(
                    "travelers_count must be a positive integer."
                )

            if "travelers" not in data:
                raise ValidationError(
                    "travelers must be provided when changing travelers_count."
                )

            current_count = booking["travelers_count"]
            seat_difference = travelers_count - current_count

            if seat_difference > 0:
                seats_held = self.tour_repository.hold_seats(
                    booking["tour_id"],
                    seat_difference,
                )

                if not seats_held:
                    raise TourOpsError(
                        "Not enough seats available.",
                        code="CONFLICT",
                        http_status=409,
                    )

            elif seat_difference < 0:
                seats_released = self.tour_repository.release_seats(
                    booking["tour_id"],
                    abs(seat_difference),
                )

                if not seats_released:
                    raise TourOpsError(
                        "Unable to release held seats.",
                        code="CONFLICT",
                        http_status=409,
                    )

            updates["travelers_count"] = travelers_count

        if "travelers" in data:
            travelers = data["travelers"]

            if not isinstance(travelers, list):
                raise ValidationError(
                    "travelers must be a list."
                )

            final_count = data.get(
                "travelers_count",
                booking["travelers_count"],
            )

            if len(travelers) != final_count:
                raise ValidationError(
                    "Travelers count does not match the number of travelers."
                )

            updates["travelers"] = travelers

            if "pricing" in data:
                validated_pricing = self._validate_pricing(
                    data["pricing"],
                    final_count,
                )

                updates["pricing"] = {
                    "unit_price": to_decimal128(validated_pricing["unit_price"]),
                    "subtotal": to_decimal128(validated_pricing["subtotal"]),
                    "discount_type": validated_pricing["discount_type"],
                    "discount_value": to_decimal128(validated_pricing["discount_value"]),
                    "discount_amount": to_decimal128(validated_pricing["discount_amount"]),
                    "discount_reason": validated_pricing["discount_reason"],
                    "discount_applied_by": validated_pricing["discount_applied_by"],
                    "taxable_amount": to_decimal128(validated_pricing["taxable_amount"]),
                    "tax_id": validated_pricing["tax_id"],
                    "tax_rate": to_decimal128(validated_pricing["tax_rate"]),
                    "tax_amount": to_decimal128(validated_pricing["tax_amount"]),
                    "total_amount": to_decimal128(validated_pricing["total_amount"]),
                }

        if "notes" in data:
            updates["notes"] = data["notes"]

        if user and user.get("id"):
            updates["updated_by"] = ObjectId(user["id"])

        updates["updated_at"] = utcnow()

        try:
            updated_booking = self.repository.update_by_id(
                booking_id,
                updates,
            )

            if not updated_booking:
                raise NotFoundError("Booking not found.")

            return updated_booking

        except Exception:
            if seat_difference > 0:
                self.tour_repository.release_seats(
                    booking["tour_id"],
                    seat_difference,
                )
            elif seat_difference < 0:
                self.tour_repository.hold_seats(
                    booking["tour_id"],
                    abs(seat_difference),
                )

            raise


    def create(self, data: dict, user=None):
     try:
        customer_id = parse_object_id(
            data["customer_id"],
            field="customer_id",
        )
        tour_id = parse_object_id(
            data["tour_id"],
            field="tour_id",
        )
     except (ValueError, TypeError) as exc:
        raise ValidationError(str(exc)) from exc

     customer = self.customer_repository.find_by_id(str(customer_id))

     if not customer:
        raise NotFoundError("Customer not found.")

     if customer.get("is_deleted", False):
        raise NotFoundError("Customer not found.")

     if customer.get("status") != "ACTIVE":
        raise ValidationError("Customer is not active.")

     tour = self.tour_repository.find_by_id(str(tour_id))

     if not tour:
        raise NotFoundError("Tour not found.")

     if tour.get("is_deleted", False):
        raise NotFoundError("Tour not found.")

     if tour.get("status") != "AVAILABLE":
        raise ValidationError("Tour is not available for booking.")

     travelers_count = data.get("travelers_count")

     if (
    isinstance(travelers_count, bool)
    or not isinstance(travelers_count, int)
    or travelers_count <= 0
):
        raise ValidationError(
        "travelers_count must be a positive integer."
    )

     available_seats = (
        tour.get("capacity", 0)
        - tour.get("booked_seats", 0)
        - tour.get("held_seats", 0)
    )

     if travelers_count > available_seats:
        raise TourOpsError(
            "Not enough seats available.",
            code="CONFLICT",
            http_status=409,
        )

     travelers = data.get("travelers")

     if not isinstance(travelers, list):
      raise ValidationError(
        "travelers must be a list."
    )
     if len(travelers) != travelers_count:
      raise ValidationError(
        "Travelers count does not match the number of travelers."
    )

     pricing = data.get("pricing")

     validated_pricing = self._validate_pricing(
            pricing,
            travelers_count,
        )


     seats_held = self.tour_repository.hold_seats(
        tour_id,
        travelers_count,
    )

     if not seats_held:
        raise TourOpsError(
            "Not enough seats available.",
            code="CONFLICT",
            http_status=409,
        )

     now = utcnow()

     user_id = None
     if user and user.get("id"):
       user_id = ObjectId(user["id"])

     booking = {
        "booking_number": next_number(Collections.BOOKINGS),
        "customer_id": customer_id,
        "tour_id": tour_id,
        "travelers_count": travelers_count,
        "booking_date": now,
        "created_by": user_id,
        "created_at": now,
        "updated_at": now,
        "updated_by": user_id,
        "travelers": travelers,
        "pricing": {
        "unit_price": to_decimal128(validated_pricing["unit_price"]),
        "subtotal": to_decimal128(validated_pricing["subtotal"]),
        "discount_type": validated_pricing["discount_type"],
        "discount_value": to_decimal128(validated_pricing["discount_value"]),
        "discount_amount": to_decimal128(validated_pricing["discount_amount"]),
        "discount_reason": validated_pricing["discount_reason"],
        "discount_applied_by": None,
        "taxable_amount": to_decimal128(validated_pricing["taxable_amount"]),
        "tax_id": validated_pricing["tax_id"],
        "tax_rate": to_decimal128(validated_pricing["tax_rate"]),
        "tax_amount": to_decimal128(validated_pricing["tax_amount"]),
        "total_amount": to_decimal128(validated_pricing["total_amount"]),
    },
        "booking_status": BookingStatus.PENDING.value,
        "payment_status": PaymentStatus.UNPAID.value,
        "notes": data.get("notes"),
    }

     try:
        return self.repository.create(booking)
     except Exception:
        self.tour_repository.release_seats(
            tour_id,
            travelers_count,
        )
        raise


    def cancel(self, booking_id: str, user=None) -> dict:
            booking = self.get_item(booking_id)
    
            if booking.get("booking_status") != BookingStatus.PENDING.value:
                raise ValidationError(
                    "Only pending bookings can be cancelled."
                )
    
            seats = booking.get("travelers_count", 0)
    
            released = self.tour_repository.release_seats(
                booking["tour_id"],
                seats,
            )
    
            if not released:
                raise TourOpsError(
                    "Unable to release held seats.",
                    code="CONFLICT",
                    http_status=409,
                )
    
            updates = {
                "booking_status": BookingStatus.CANCELLED.value,
                "updated_at": utcnow(),
            }
    
            if user and user.get("id"):
                updates["updated_by"] = ObjectId(user["id"])
    
            try:
                updated_booking = self.repository.update_by_id(
                    booking_id,
                    updates,
                )
    
                if not updated_booking:
                    # If the booking update fails after releasing seats,
                    # attempt to restore the held seats.
                    self.tour_repository.hold_seats(
                        booking["tour_id"],
                        seats,
                    )
    
                    raise NotFoundError("Booking not found.")
    
                return updated_booking
    
            except Exception:
                # Restore seats if updating the booking fails.
                self.tour_repository.hold_seats(
                    booking["tour_id"],
                    seats,
                )
                raise



    def confirm(self, booking_id: str, user=None) -> dict:
        booking = self.get_item(booking_id)

        if booking.get("booking_status") != BookingStatus.PENDING.value:
            raise ValidationError(
                "Only pending bookings can be confirmed."
            )

        seats = booking.get("travelers_count", 0)

        moved = self.tour_repository.confirm_seats(
            booking["tour_id"],
            seats,
        )

        if not moved:
            raise TourOpsError(
                "Unable to confirm seats.",
                code="CONFLICT",
                http_status=409,
            )

        updates = {
            "booking_status": BookingStatus.CONFIRMED.value,
            "updated_at": utcnow(),
        }

        if user and user.get("id"):
            updates["updated_by"] = ObjectId(user["id"])

        try:
            updated_booking = self.repository.update_by_id(
                booking_id,
                updates,
            )

            if not updated_booking:
                # Restore the seat state if the booking update fails.
                self.tour_repository.restore_held_seats(
                    booking["tour_id"],
                    seats,
                )

                raise NotFoundError("Booking not found.")

            return updated_booking

        except Exception:
            self.tour_repository.restore_held_seats(
                booking["tour_id"],
                seats,
            )
            raise