from core.constants import RoomType, SupplierReservationStatus, SupplierType

FIELD_CLASS = "field"

STATUS_LABELS = {
    SupplierReservationStatus.REQUESTED.value: "Requested",
    SupplierReservationStatus.CONFIRMED.value: "Confirmed",
    SupplierReservationStatus.CANCELLED.value: "Cancelled",
}
STATUS_CHOICES = tuple(STATUS_LABELS.items())

ROOM_TYPE_LABELS = {
    RoomType.SINGLE.value: "Single",
    RoomType.TWIN.value: "Twin",
    RoomType.DOUBLE.value: "Double",
    RoomType.TRIPLE.value: "Triple",
    RoomType.QUAD.value: "Quad",
}
ROOM_TYPE_CHOICES = tuple(ROOM_TYPE_LABELS.items())

DEFAULT_OCCUPANCY = {
    RoomType.SINGLE.value: 1,
    RoomType.TWIN.value: 2,
    RoomType.DOUBLE.value: 2,
    RoomType.TRIPLE.value: 3,
    RoomType.QUAD.value: 4,
}

SERVICE_TYPE_LABELS = {
    SupplierType.HOTEL.value: "Accommodation",
    SupplierType.TRANSPORTATION.value: "Transportation",
    SupplierType.TOUR_GUIDE.value: "Guide",
    SupplierType.AIRLINE.value: "Airline",
    SupplierType.ACTIVITY_PROVIDER.value: "Activity",
    SupplierType.RESTAURANT.value: "Restaurant",
    SupplierType.INSURANCE.value: "Insurance",
    SupplierType.OTHER.value: "Other",
}
