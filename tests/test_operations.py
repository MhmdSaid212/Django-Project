import json
from decimal import Decimal

from django.urls import reverse

from apps.bookings.services import BookingService
from apps.customers.services import CustomerService
from apps.invoices.services import InvoiceService
from apps.supplier_reservations.services import SupplierReservationService
from apps.suppliers.services import SupplierService
from apps.tours.services import TourService
from core.constants import BookingStatus, SupplierReservationStatus, SupplierType
from core.exceptions import BusinessRuleViolation, ValidationError
from core.money import to_money


OWNER_ID = "000000000000000000000001"


def _tour(**overrides):
    payload = {
        "actor_id": OWNER_ID,
        "name": "Egypt Discovery",
        "city": "Cairo",
        "country": "Egypt",
        "start_date": "2026-09-12",
        "end_date": "2026-09-18",
        "capacity": 50,
        "selling_price_per_person": "900.00",
    }
    payload.update(overrides)
    return TourService().create(**payload)


def _hotel(**overrides):
    payload = {
        "actor_id": OWNER_ID,
        "name": "Nile View Hotel",
        "supplier_type": SupplierType.HOTEL.value,
        "email": "stay@nileview.example",
        "city": "Cairo",
        "country": "Egypt",
    }
    payload.update(overrides)
    return SupplierService().create(**payload)


def _second_hotel():
    return _hotel(name="Pyramids Hotel", email="stay@pyramids.example")


def _customer(**overrides):
    payload = {
        "actor_id": OWNER_ID,
        "first_name": "Fatima",
        "last_name": "Ghazzawi",
        "email": "fatima@example.com",
        "phone": "+20 100 000 0000",
        "city": "Cairo",
        "country": "Egypt",
    }
    payload.update(overrides)
    return CustomerService().create(**payload)


def _travelers(*names):
    people = []
    for name in names:
        first, last = name.split(" ", 1)
        people.append({"first_name": first, "last_name": last, "passport_number": f"P-{first[:2].upper()}1"})
    return people


def _booking(tour, customer, names, *, confirm=False):
    booking = BookingService().create(
        actor_id=OWNER_ID,
        customer_id=tour and customer["_id"],
        tour_id=tour["_id"],
        travelers=_travelers(*names),
    )
    if confirm:
        booking = BookingService().confirm(booking["_id"], actor_id=OWNER_ID)
    return booking


def _hotel_reservation(tour, hotel, *, allocations=None, status="REQUESTED", confirmation="NV-4410"):
    return SupplierReservationService().create(
        actor_id=OWNER_ID,
        tour_id=tour["_id"],
        supplier_id=hotel["_id"],
        room_allocations=allocations
        or [
            {"room_type": "SINGLE", "quantity": 5, "occupancy": 1},
            {"room_type": "TWIN", "quantity": 15, "occupancy": 2},
            {"room_type": "TRIPLE", "quantity": 5, "occupancy": 3},
        ],
        status=status,
        confirmation_number=confirmation if status == SupplierReservationStatus.CONFIRMED.value else None,
        release_date="2026-09-01",
    )


def test_confirm_booking_uses_tour_seats_not_rooms():
    tour = _tour(capacity=4)
    customer = _customer()
    booking = _booking(tour, customer, ["Fatima Ghazzawi", "Waad Nasser"], confirm=True)
    tour = TourService().get(tour["_id"])
    assert booking["booking_status"] == BookingStatus.CONFIRMED.value
    assert tour["booked_seats"] == 2
    assert tour["capacity"] == 4


def test_confirm_refuses_over_capacity():
    tour = _tour(capacity=2)
    customer = _customer()
    _booking(tour, customer, ["Fatima Ghazzawi", "Waad Nasser"], confirm=True)
    other = CustomerService().create(
        actor_id=OWNER_ID, first_name="Omar", last_name="Said", email="omar@example.com"
    )
    booking = _booking(tour, other, ["Omar Said"])
    try:
        BookingService().confirm(booking["_id"], actor_id=OWNER_ID)
    except BusinessRuleViolation as extra:
        assert "seats" in extra.message.lower()
    else:
        raise AssertionError("expected BusinessRuleViolation")
    assert TourService().get(tour["_id"])["booked_seats"] == 2


def test_cancel_confirmed_booking_restores_seats():
    tour = _tour(capacity=10)
    customer = _customer()
    booking = _booking(tour, customer, ["Fatima Ghazzawi", "Waad Nasser"], confirm=True)
    BookingService().cancel(booking["_id"], actor_id=OWNER_ID)
    assert TourService().get(tour["_id"])["booked_seats"] == 0
    assert BookingService().get(booking["_id"])["booking_status"] == BookingStatus.CANCELLED.value


def test_cancel_pending_does_not_change_seats():
    tour = _tour()
    customer = _customer()
    booking = _booking(tour, customer, ["Fatima Ghazzawi"])
    BookingService().cancel(booking["_id"], actor_id=OWNER_ID)
    assert TourService().get(tour["_id"])["booked_seats"] == 0


def test_invoice_only_after_confirm():
    tour = _tour()
    customer = _customer()
    booking = _booking(tour, customer, ["Fatima Ghazzawi"])
    try:
        InvoiceService().create_for_booking(str(booking["_id"]), created_by=OWNER_ID)
    except BusinessRuleViolation:
        pass
    else:
        raise AssertionError("expected BusinessRuleViolation")
    BookingService().confirm(booking["_id"], actor_id=OWNER_ID)
    invoice = InvoiceService().create_for_booking(str(booking["_id"]), created_by=OWNER_ID)
    assert invoice["invoice_number"].startswith("INV-")
    assert to_money(invoice["total_amount"]) == Decimal("900.00")


def test_hotel_allocation_is_rooms_not_travelers():
    tour = _tour()
    hotel = _hotel()
    reservation = _hotel_reservation(tour, hotel)
    presented = SupplierReservationService().get_presented(reservation["_id"])
    assert presented["room_count"] == 25
    assert presented["bed_capacity"] == 5 + 30 + 15
    assert TourService().get(tour["_id"])["capacity"] == 50


def test_multiple_hotels_on_one_tour():
    tour = _tour()
    first = _hotel()
    second = _second_hotel()
    _hotel_reservation(
        tour,
        first,
        allocations=[{"room_type": "TWIN", "quantity": 15, "occupancy": 2}],
    )
    _hotel_reservation(
        tour,
        second,
        allocations=[{"room_type": "TWIN", "quantity": 5, "occupancy": 2}],
    )
    rows = SupplierReservationService().list_for_tour(tour["_id"])
    assert len(rows) == 2
    snapshot = SupplierReservationService().accommodation_snapshot(tour["_id"])
    assert snapshot["room_count"] == 20
    assert snapshot["bed_capacity"] == 40


def test_shortage_warning_uses_occupancy_not_room_count():
    tour = _tour(capacity=50)
    hotel = _hotel()
    _hotel_reservation(
        tour,
        hotel,
        allocations=[{"room_type": "SINGLE", "quantity": 2, "occupancy": 1}],
        status=SupplierReservationStatus.CONFIRMED.value,
    )
    customer = _customer()
    _booking(tour, customer, ["Fatima Ghazzawi", "Waad Nasser", "Omar Said"], confirm=True)
    snapshot = SupplierReservationService().accommodation_snapshot(tour["_id"])
    assert snapshot["confirmed_travelers"] == 3
    assert snapshot["bed_capacity"] == 2
    assert snapshot["shortage_travelers"] == 1
    assert any("insufficient for 1" in warning for warning in snapshot["warnings"])
    assert TourService().get(tour["_id"])["capacity"] == 50


def test_reservation_does_not_create_expense():
    tour = _tour()
    hotel = _hotel()
    _hotel_reservation(tour, hotel, status=SupplierReservationStatus.CONFIRMED.value)
    from core.database import get_collection
    from core.constants import Collections

    assert get_collection(Collections.EXPENSES).count_documents({}) == 0
    assert get_collection(Collections.SUPPLIER_PAYMENTS).count_documents({}) == 0


def test_rooming_list_reuses_booking_travelers():
    tour = _tour()
    hotel = _hotel()
    reservation = _hotel_reservation(tour, hotel, status=SupplierReservationStatus.CONFIRMED.value)
    customer = _customer()
    booking = _booking(tour, customer, ["Fatima Ghazzawi", "Waad Nasser"], confirm=True)
    BookingService().assign_rooms(
        booking["_id"],
        [
            {
                "traveler_index": 0,
                "room_number": "101",
                "room_type": "TWIN",
                "hotel_reservation_id": reservation["_id"],
            },
            {
                "traveler_index": 1,
                "room_number": "101",
                "room_type": "TWIN",
                "hotel_reservation_id": reservation["_id"],
            },
        ],
        actor_id=OWNER_ID,
        tour_id=tour["_id"],
    )
    listing = SupplierReservationService().rooming_list(tour["_id"])
    assert listing["rooms"][0]["room_number"] == "101"
    names = [guest["name"] for guest in listing["rooms"][0]["guests"]]
    assert names == ["Fatima Ghazzawi", "Waad Nasser"]


def test_hotel_needs_allocation():
    tour = _tour()
    hotel = _hotel()
    try:
        SupplierReservationService().create(
            actor_id=OWNER_ID,
            tour_id=tour["_id"],
            supplier_id=hotel["_id"],
            room_allocations=[],
        )
    except ValidationError as extra:
        assert "room type" in extra.message.lower()
    else:
        raise AssertionError("expected ValidationError")


def test_html_reservation_and_rooming_pages(owner_session):
    tour = _tour()
    hotel = _hotel()
    reservation = _hotel_reservation(tour, hotel)
    response = owner_session.get(reverse("tours:detail", args=[str(tour["_id"])]) + "?tab=reservations")
    assert response.status_code == 200
    assert b"Arrange supplier" in response.content
    response = owner_session.get(reverse("supplier_reservations:detail", args=[str(reservation["_id"])]))
    assert response.status_code == 200
    assert b"Nile View Hotel" in response.content
    response = owner_session.get(reverse("supplier_reservations:rooming", args=[str(tour["_id"])]))
    assert response.status_code == 200
    assert b"Rooming list" in response.content


def test_api_create_and_confirm_reservation(owner_session):
    tour = _tour()
    hotel = _hotel()
    create = owner_session.post(
        reverse("tours_api:reservations", args=[str(tour["_id"])]),
        data=json.dumps(
            {
                "supplier_id": str(hotel["_id"]),
                "room_allocations": [{"room_type": "TWIN", "quantity": 4, "occupancy": 2}],
            }
        ),
        content_type="application/json",
    )
    assert create.status_code == 201, create.content
    reservation_id = create.json()["data"]["id"]
    confirm = owner_session.post(
        reverse("supplier_reservations_api:confirm", args=[reservation_id]),
        data=json.dumps({"confirmation_number": "NV-4410"}),
        content_type="application/json",
    )
    assert confirm.status_code == 200
    assert confirm.json()["data"]["status"] == SupplierReservationStatus.CONFIRMED.value


def test_email_generation_uses_live_reservation_data():
    from apps.supplier_reservations.emails import SupplierEmailService

    tour = _tour(name="Egypt Explorer")
    hotel = _hotel()
    reservation = _hotel_reservation(
        tour,
        hotel,
        allocations=[{"room_type": "TWIN", "quantity": 15, "occupancy": 2}],
    )
    email = SupplierEmailService().build_reservation_request(str(reservation["_id"]))
    presented = SupplierReservationService().get_presented(reservation["_id"])
    assert email["to"] == "stay@nileview.example"
    assert "Egypt Explorer" in email["subject"]
    assert "Nile View Hotel" in email["body"]
    assert "15 Twin" in email["body"]
    assert "30" in email["body"]
    followup = SupplierEmailService().build_confirmation_followup(str(reservation["_id"]))
    assert presented["number"] in followup["subject"]
    assert presented["number"] in followup["body"]


def test_html_email_preview_and_ops_pages(owner_session):
    tour = _tour()
    hotel = _hotel()
    reservation = _hotel_reservation(tour, hotel)
    email_page = owner_session.get(reverse("supplier_reservations:email", args=[str(reservation["_id"])]))
    assert email_page.status_code == 200
    assert b"stay@nileview.example" in email_page.content
    assert b"Egypt Discovery" in email_page.content
    assert owner_session.get(reverse("supplier_reservations:rooming_index")).status_code == 200
    assert owner_session.get(reverse("tours:rooming", args=[str(tour["_id"])])).status_code == 302
    agent_dash = owner_session.get(reverse("dashboard:agent"))
    assert agent_dash.status_code == 200
    assert b"Requested" in agent_dash.content


def test_accountant_cannot_open_supplier_reservations(accountant_session):
    assert accountant_session.get(reverse("supplier_reservations:list")).status_code == 403
    assert accountant_session.get(reverse("expenses:list")).status_code == 200


def test_agent_can_open_reservations_not_expenses(agent_session):
    assert agent_session.get(reverse("supplier_reservations:list")).status_code == 200
    assert agent_session.get(reverse("expenses:list")).status_code == 403


def test_html_confirm_does_not_create_expense_or_change_seats(owner_session):
    tour = _tour(capacity=10)
    customer = _customer()
    _booking(tour, customer, ["Fatima Ghazzawi"], confirm=True)
    hotel = _hotel()
    reservation = _hotel_reservation(tour, hotel)
    before = TourService().get(tour["_id"])["booked_seats"]
    missing = owner_session.post(
        reverse("supplier_reservations:confirm", args=[str(reservation["_id"])]),
        {},
    )
    assert missing.status_code == 302
    assert SupplierReservationService().get_presented(reservation["_id"])["status"] == SupplierReservationStatus.REQUESTED.value
    response = owner_session.post(
        reverse("supplier_reservations:confirm", args=[str(reservation["_id"])]),
        {"confirmation_number": "NVH-7821"},
    )
    assert response.status_code == 302
    presented = SupplierReservationService().get_presented(reservation["_id"])
    assert presented["status"] == SupplierReservationStatus.CONFIRMED.value
    assert presented["confirmation_number"] == "NVH-7821"
    assert TourService().get(tour["_id"])["booked_seats"] == before
    from core.constants import Collections
    from core.database import get_collection

    assert get_collection(Collections.EXPENSES).count_documents({}) == 0


def test_html_cancel_does_not_change_seats(owner_session):
    tour = _tour(capacity=10)
    customer = _customer()
    _booking(tour, customer, ["Fatima Ghazzawi"], confirm=True)
    hotel = _hotel()
    reservation = _hotel_reservation(tour, hotel, status=SupplierReservationStatus.CONFIRMED.value)
    before = TourService().get(tour["_id"])["booked_seats"]
    response = owner_session.post(reverse("supplier_reservations:cancel", args=[str(reservation["_id"])]))
    assert response.status_code == 302
    assert SupplierReservationService().get_presented(reservation["_id"])["status"] == SupplierReservationStatus.CANCELLED.value
    assert TourService().get(tour["_id"])["booked_seats"] == before
