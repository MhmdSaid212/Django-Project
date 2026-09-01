from core.constants import RecordStatus, SupplierType

FIELD_CLASS = "field"

TYPE_LABELS = {
    SupplierType.HOTEL.value: "Hotel",
    SupplierType.TRANSPORTATION.value: "Transportation",
    SupplierType.TOUR_GUIDE.value: "Guide",
    SupplierType.AIRLINE.value: "Airline",
    SupplierType.ACTIVITY_PROVIDER.value: "Activity",
    SupplierType.RESTAURANT.value: "Restaurant",
    SupplierType.INSURANCE.value: "Insurance",
    SupplierType.OTHER.value: "Other",
}
TYPE_CHOICES = tuple(TYPE_LABELS.items())

STATUS_CHOICES = (
    (RecordStatus.ACTIVE.value, "Active"),
    (RecordStatus.INACTIVE.value, "Inactive"),
)

CORE_TYPES = (
    SupplierType.HOTEL.value,
    SupplierType.TRANSPORTATION.value,
    SupplierType.TOUR_GUIDE.value,
)
OTHER_GROUP_TYPES = tuple(item.value for item in SupplierType if item.value not in CORE_TYPES)

DIRECTORY_TYPES = {
    "HOTEL": (SupplierType.HOTEL.value,),
    "TRANSPORTATION": (SupplierType.TRANSPORTATION.value,),
    "TOUR_GUIDE": (SupplierType.TOUR_GUIDE.value,),
    "OTHER": OTHER_GROUP_TYPES,
}

INFO_FIELDS = {
    SupplierType.HOTEL.value: (
        "star_rating",
        "room_count",
        "room_types",
        "check_in_time",
        "check_out_time",
        "amenities",
        "board_basis",
    ),
    SupplierType.TRANSPORTATION.value: (
        "vehicle_type",
        "fleet_size",
        "seats_per_vehicle",
        "license_number",
        "coverage_areas",
    ),
    SupplierType.TOUR_GUIDE.value: (
        "languages",
        "license_number",
        "specialties",
        "years_experience",
    ),
    SupplierType.AIRLINE.value: ("iata_code", "alliance"),
    SupplierType.ACTIVITY_PROVIDER.value: ("activity_kinds", "typical_duration_hours", "location"),
    SupplierType.RESTAURANT.value: ("cuisine", "seating_capacity", "meal_types"),
    SupplierType.INSURANCE.value: ("policy_types", "coverage_notes"),
    SupplierType.OTHER.value: ("details",),
}

LIST_INFO_FIELDS = {
    "room_types",
    "amenities",
    "coverage_areas",
    "languages",
    "specialties",
    "activity_kinds",
    "meal_types",
    "policy_types",
}
INT_INFO_FIELDS = {
    "star_rating",
    "room_count",
    "fleet_size",
    "seats_per_vehicle",
    "years_experience",
    "typical_duration_hours",
    "seating_capacity",
}
