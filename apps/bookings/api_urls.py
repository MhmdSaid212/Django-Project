from django.urls import path

from apps.bookings import api
from apps.invoices.api import create_invoice_for_booking
from core.http import method_view

app_name = "bookings_api"

urlpatterns = [
    path("", method_view(GET=api.list_bookings, POST=api.create_booking), name="collection"),
    path("<str:id>/confirm/", method_view(POST=api.confirm_booking), name="confirm"),
    path("<str:id>/cancel/", method_view(POST=api.cancel_booking), name="cancel"),
    path("<str:booking_id>/invoice/", method_view(POST=create_invoice_for_booking), name="invoice"),
    path("<str:id>/", method_view(GET=api.get_booking, PATCH=api.patch_booking), name="detail"),
]
