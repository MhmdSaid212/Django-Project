from django.urls import path

from apps.invoices import api
from apps.payments.api import create_payment_for_invoice, payments_for_invoice
from core.http import method_view

app_name = "invoices_api"

urlpatterns = [
    path("", method_view(GET=api.list_invoices, POST=api.create_invoice), name="collection"),
    path(
        "<str:invoice_id>/payments/",
        method_view(GET=payments_for_invoice, POST=create_payment_for_invoice),
        name="payments",
    ),
    path("<str:id>/", method_view(GET=api.get_invoice, PATCH=api.patch_invoice), name="detail"),
]
