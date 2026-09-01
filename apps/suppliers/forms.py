from django import forms

from apps.suppliers.constants import FIELD_CLASS, STATUS_CHOICES, TYPE_CHOICES
from apps.suppliers.validators import join_list


def _styled(fields: dict[str, forms.Field]) -> None:
    for field in fields.values():
        existing = field.widget.attrs.get("class", "")
        classes = existing.split()
        if FIELD_CLASS not in classes:
            classes.append(FIELD_CLASS)
        field.widget.attrs["class"] = " ".join(dict.fromkeys(classes))


class SupplierForm(forms.Form):
    name = forms.CharField(max_length=200, label="Company name")
    supplier_type = forms.ChoiceField(choices=TYPE_CHOICES, label="Type")
    contact_person = forms.CharField(required=False, max_length=120, label="Contact")
    email = forms.EmailField(required=False)
    phone = forms.CharField(required=False, max_length=40)
    country = forms.CharField(required=False, max_length=80)
    city = forms.CharField(required=False, max_length=80)
    street = forms.CharField(required=False, max_length=200)
    tax_number = forms.CharField(required=False, max_length=80, label="Tax number")
    payment_terms = forms.CharField(required=False, max_length=80, label="Payment terms")
    bank_name = forms.CharField(required=False, max_length=120)
    account_name = forms.CharField(required=False, max_length=120)
    iban = forms.CharField(required=False, max_length=80, label="IBAN")
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)

    star_rating = forms.IntegerField(required=False, min_value=0, max_value=5, label="Stars")
    room_count = forms.IntegerField(required=False, min_value=0, label="Rooms")
    board_basis = forms.CharField(required=False, max_length=40, label="Board")
    check_in_time = forms.CharField(required=False, max_length=20, label="Check-in")
    check_out_time = forms.CharField(required=False, max_length=20, label="Check-out")
    room_types = forms.CharField(required=False, label="Room types")
    amenities = forms.CharField(required=False)

    vehicle_type = forms.CharField(required=False, max_length=80, label="Vehicle type")
    fleet_size = forms.IntegerField(required=False, min_value=0, label="Fleet size")
    seats_per_vehicle = forms.IntegerField(required=False, min_value=0, label="Seats / vehicle")
    license_number = forms.CharField(required=False, max_length=80, label="License number")
    coverage_areas = forms.CharField(required=False, label="Coverage areas")

    languages = forms.CharField(required=False)
    years_experience = forms.IntegerField(required=False, min_value=0, label="Years")
    specialties = forms.CharField(required=False)
    guide_license_number = forms.CharField(required=False, max_length=80, label="License number")

    iata_code = forms.CharField(required=False, max_length=8, label="IATA code")
    alliance = forms.CharField(required=False, max_length=80)

    activity_kinds = forms.CharField(required=False, label="Activity kinds")
    typical_duration_hours = forms.IntegerField(required=False, min_value=0, label="Typical duration (hours)")
    location = forms.CharField(required=False, max_length=120)

    cuisine = forms.CharField(required=False, max_length=80)
    seating_capacity = forms.IntegerField(required=False, min_value=0, label="Seating capacity")
    meal_types = forms.CharField(required=False, label="Meal types")

    policy_types = forms.CharField(required=False, label="Policy types")
    coverage_notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}), label="Coverage notes")

    details = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, include_status=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not include_status:
            self.fields.pop("status")
        self.fields["payment_terms"].widget.attrs.setdefault("placeholder", "Net 14")
        self.fields["room_types"].widget.attrs.setdefault("placeholder", "double, twin, suite")
        self.fields["amenities"].widget.attrs.setdefault("placeholder", "wifi, pool, breakfast")
        self.fields["languages"].widget.attrs.setdefault("placeholder", "Arabic, English")
        self.fields["specialties"].widget.attrs.setdefault("placeholder", "history, museums")
        _styled(self.fields)


def initial_from_record(record: dict) -> dict:
    info = record.get("info") or {}
    address = record.get("address") or {}
    bank = record.get("bank_details") or {}
    return {
        "name": record.get("name") or "",
        "supplier_type": record.get("type") or record.get("supplier_type") or "",
        "contact_person": record.get("contact_person") or "",
        "email": record.get("email") or "",
        "phone": record.get("phone") or "",
        "country": record.get("country") or address.get("country") or "",
        "city": record.get("city") or address.get("city") or "",
        "street": record.get("street") or address.get("street") or "",
        "tax_number": record.get("tax_number") or "",
        "payment_terms": record.get("payment_terms") or "",
        "bank_name": bank.get("bank_name") or "",
        "account_name": bank.get("account_name") or "",
        "iban": bank.get("iban") or "",
        "notes": record.get("notes") or "",
        "status": record.get("status") or "",
        "star_rating": info.get("star_rating"),
        "room_count": info.get("room_count"),
        "board_basis": info.get("board_basis") or "",
        "check_in_time": info.get("check_in_time") or "",
        "check_out_time": info.get("check_out_time") or "",
        "room_types": join_list(info.get("room_types")),
        "amenities": join_list(info.get("amenities")),
        "vehicle_type": info.get("vehicle_type") or "",
        "fleet_size": info.get("fleet_size"),
        "seats_per_vehicle": info.get("seats_per_vehicle"),
        "license_number": info.get("license_number") or "",
        "coverage_areas": join_list(info.get("coverage_areas")),
        "languages": join_list(info.get("languages")),
        "years_experience": info.get("years_experience"),
        "specialties": join_list(info.get("specialties")),
        "guide_license_number": info.get("license_number") or "",
        "iata_code": info.get("iata_code") or "",
        "alliance": info.get("alliance") or "",
        "activity_kinds": join_list(info.get("activity_kinds")),
        "typical_duration_hours": info.get("typical_duration_hours"),
        "location": info.get("location") or "",
        "cuisine": info.get("cuisine") or "",
        "seating_capacity": info.get("seating_capacity"),
        "meal_types": join_list(info.get("meal_types")),
        "policy_types": join_list(info.get("policy_types")),
        "coverage_notes": info.get("coverage_notes") or "",
        "details": info.get("details") or "",
    }
