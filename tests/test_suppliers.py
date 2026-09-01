import json
from decimal import Decimal

from bson import ObjectId
from django.urls import reverse

from apps.expenses.services import ExpenseService
from apps.suppliers.services import SupplierService
from core.constants import ExpenseCategory, ExpenseScope, SupplierType
from core.exceptions import NotFoundError, ValidationError
from core.money import ZERO, to_money


OWNER_ID = "000000000000000000000001"


def _create_hotel(**overrides):
    payload = {
        "actor_id": OWNER_ID,
        "name": "Nile View Hotel",
        "supplier_type": SupplierType.HOTEL.value,
        "contact_person": "Sara Ali",
        "email": "reservations@nileview.example",
        "phone": "+20 2 555 0100",
        "country": "Egypt",
        "city": "Cairo",
        "street": "Corniche El Nile",
        "payment_terms": "Net 14",
        "bank_name": "Banque Misr",
        "iban": "EG123",
        "star_rating": 4,
        "room_count": 120,
        "board_basis": "BB",
        "check_in_time": "14:00",
        "check_out_time": "12:00",
        "room_types": "double, twin, suite",
        "amenities": "wifi, pool, breakfast",
    }
    payload.update(overrides)
    return SupplierService().create(**payload)


def _create_guide(**overrides):
    payload = {
        "actor_id": OWNER_ID,
        "name": "Hassan Farouk",
        "supplier_type": SupplierType.TOUR_GUIDE.value,
        "contact_person": "Hassan Farouk",
        "city": "Luxor",
        "country": "Egypt",
        "languages": "Arabic, English",
        "years_experience": 12,
        "specialties": "history, temples",
    }
    payload.update(overrides)
    return SupplierService().create(**payload)


def _create_airline(**overrides):
    payload = {
        "actor_id": OWNER_ID,
        "name": "EgyptAir",
        "supplier_type": SupplierType.AIRLINE.value,
        "city": "Cairo",
        "country": "Egypt",
        "iata_code": "MS",
    }
    payload.update(overrides)
    return SupplierService().create(**payload)


def _bill_supplier(supplier, amount="3000.00"):
    return ExpenseService().create(
        actor_id=OWNER_ID,
        expense_scope=ExpenseScope.GENERAL.value,
        category=ExpenseCategory.HOTEL.value,
        amount=amount,
        description="Supplier bill",
        expense_date="2026-08-20",
        supplier_id=supplier["_id"],
    )


def test_create_hotel_and_guide_numbers():
    hotel = _create_hotel()
    guide = _create_guide()
    assert hotel["supplier_number"] == "SUP-1001"
    assert hotel["supplier_type"] == SupplierType.HOTEL.value
    assert hotel["hotel_info"]["star_rating"] == 4
    assert hotel["hotel_info"]["room_types"] == ["double", "twin", "suite"]
    assert hotel["tour_guide_info"] is None
    assert guide["supplier_number"] == "SUP-1002"
    assert guide["tour_guide_info"]["languages"] == ["Arabic", "English"]
    assert guide["tour_guide_info"]["years_experience"] == 12


def test_create_requires_name():
    try:
        SupplierService().create(actor_id=OWNER_ID, name="  ", supplier_type="HOTEL")
    except ValidationError as extra:
        assert "name" in extra.message.lower()
    else:
        raise AssertionError("expected ValidationError")


def test_list_filters_by_type_and_other_group():
    _create_hotel()
    _create_guide()
    airline = _create_airline()
    hotels = SupplierService().list_presented(supplier_type="HOTEL")
    guides = SupplierService().list_presented(supplier_type="TOUR_GUIDE")
    other = SupplierService().list_presented(group="OTHER")
    assert len(hotels) == 1
    assert hotels[0]["name"] == "Nile View Hotel"
    assert len(guides) == 1
    assert [row["id"] for row in other] == [str(airline["_id"])]


def test_owed_comes_from_open_expenses():
    hotel = _create_hotel()
    _create_hotel(name="Quiet Inn")
    _bill_supplier(hotel, "3000.00")
    rows = {row["name"]: row for row in SupplierService().list_presented()}
    assert to_money(rows["Nile View Hotel"]["owed"]) == Decimal("3000.00")
    assert to_money(rows["Quiet Inn"]["owed"]) == ZERO
    presented = SupplierService().get_presented(hotel["_id"])
    assert presented["has_balance"] is True
    assert len(presented["open_expenses"]) == 1
    assert presented["open_expenses"][0]["number"] == "EXP-1001"


def test_cannot_delete_supplier_with_balance():
    hotel = _create_hotel()
    _bill_supplier(hotel)
    try:
        SupplierService().soft_delete(hotel["_id"], actor_id=OWNER_ID)
    except ValidationError as extra:
        assert "balance" in extra.message.lower()
    else:
        raise AssertionError("expected ValidationError")


def test_soft_delete_hides_supplier():
    hotel = _create_hotel()
    SupplierService().soft_delete(hotel["_id"], actor_id=OWNER_ID)
    try:
        SupplierService().get(hotel["_id"])
    except NotFoundError:
        pass
    else:
        raise AssertionError("expected NotFoundError")
    assert SupplierService().list_items() == []


def test_patch_phone_keeps_city_and_hotel_info():
    hotel = _create_hotel()
    updated = SupplierService().update(hotel["_id"], phone="+20 100 000 0000")
    assert updated["phone"] == "+20 100 000 0000"
    assert updated["address"]["city"] == "Cairo"
    assert updated["hotel_info"]["star_rating"] == 4


def test_agent_and_accountant_can_open_suppliers(agent_session, accountant_session):
    assert agent_session.get(reverse("suppliers:list")).status_code == 200
    assert accountant_session.get(reverse("suppliers:list")).status_code == 200
    create = agent_session.get(reverse("suppliers:create"))
    assert create.status_code == 200
    assert b"New supplier" in create.content


def test_html_create_detail_and_directories(owner_session):
    response = owner_session.post(
        reverse("suppliers:create"),
        {
            "name": "Nile View Hotel",
            "supplier_type": SupplierType.HOTEL.value,
            "contact_person": "Sara Ali",
            "email": "reservations@nileview.example",
            "phone": "+20 2 555 0100",
            "country": "Egypt",
            "city": "Cairo",
            "payment_terms": "Net 14",
            "star_rating": "4",
            "room_count": "120",
            "board_basis": "BB",
        },
    )
    assert response.status_code == 302, response.content
    hotel = SupplierService().list_items()[0]
    assert hotel["supplier_number"] == "SUP-1001"
    detail = owner_session.get(reverse("suppliers:detail", args=[str(hotel["_id"])]))
    assert detail.status_code == 200
    assert b"SUP-1001" in detail.content
    assert b"Nile View Hotel" in detail.content
    assert b"BB" in detail.content
    listing = owner_session.get(reverse("suppliers:list"))
    assert b"SUP-1001" in listing.content
    hotels = owner_session.get(reverse("suppliers:hotels"))
    assert hotels.status_code == 200
    assert b"Nile View Hotel" in hotels.content


def test_html_other_directory_includes_airline(owner_session):
    _create_hotel()
    airline = _create_airline()
    response = owner_session.get(reverse("suppliers:other"))
    assert response.status_code == 200
    assert b"EgyptAir" in response.content
    assert b"Nile View Hotel" not in response.content
    assert str(airline["_id"]).encode() in response.content or b"SUP-1002" in response.content


def test_html_unknown_id_redirects(owner_session):
    response = owner_session.get(reverse("suppliers:detail", args=["sup-1001"]))
    assert response.status_code == 302
    assert reverse("suppliers:list") in response["Location"]


def test_html_empty_list(owner_session):
    response = owner_session.get(reverse("suppliers:list"))
    assert response.status_code == 200
    assert b"No suppliers yet" in response.content


def test_api_create_list_get_patch(owner_session):
    create = owner_session.post(
        "/api/suppliers/",
        data=json.dumps(
            {
                "name": "Nile View Hotel",
                "type": "HOTEL",
                "city": "Cairo",
                "country": "Egypt",
                "hotel_info": {"star_rating": 4, "room_count": 120, "board_basis": "BB"},
            }
        ),
        content_type="application/json",
    )
    assert create.status_code == 201, create.content
    body = create.json()
    assert body["success"] is True
    assert body["data"]["number"] == "SUP-1001"
    assert body["data"]["type"] == "HOTEL"
    assert body["data"]["info"]["star_rating"] == 4
    supplier_id = body["data"]["id"]

    listing = owner_session.get("/api/suppliers/?supplier_type=HOTEL")
    assert listing.status_code == 200
    assert len(listing.json()["data"]["suppliers"]) == 1

    other = owner_session.get("/api/suppliers/?group=OTHER")
    assert other.status_code == 200
    assert other.json()["data"]["suppliers"] == []

    detail = owner_session.get(f"/api/suppliers/{supplier_id}/")
    assert detail.status_code == 200
    assert detail.json()["data"]["city"] == "Cairo"

    patch = owner_session.patch(
        f"/api/suppliers/{supplier_id}/",
        data=json.dumps({"phone": "+20 2 555 0100"}),
        content_type="application/json",
    )
    assert patch.status_code == 200
    assert patch.json()["data"]["phone"] == "+20 2 555 0100"
    assert patch.json()["data"]["city"] == "Cairo"
    assert patch.json()["data"]["info"]["star_rating"] == 4


def test_api_unknown_id_is_404(owner_session):
    response = owner_session.get(f"/api/suppliers/{ObjectId()}/")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_api_rejects_invalid_json(owner_session):
    response = owner_session.post("/api/suppliers/", data="{", content_type="application/json")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_record_payment_filters_expenses_by_supplier(owner_session):
    hotel = _create_hotel()
    guide = _create_guide()
    hotel_bill = _bill_supplier(hotel, "1500.00")
    _bill_supplier(guide, "400.00")
    response = owner_session.get(reverse("supplier_payments:create") + f"?supplier_id={hotel['_id']}")
    assert response.status_code == 200
    assert hotel_bill["expense_number"].encode() in response.content
    assert b"EXP-1002" not in response.content
