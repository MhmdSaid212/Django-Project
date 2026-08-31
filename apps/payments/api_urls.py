from django.urls import path

from apps.payments import api
from apps.receipts.api import receipt_for_payment
from apps.refunds.api import refund_from_payment
from core.http import method_view

app_name = "payments_api"

urlpatterns = [
    path("", method_view(GET=api.list_payments, POST=api.create_payment), name="collection"),
    path("<str:payment_id>/receipt/", method_view(GET=receipt_for_payment), name="receipt"),
    path("<str:payment_id>/refund/", method_view(POST=refund_from_payment), name="refund"),
    path("<str:id>/", method_view(GET=api.get_payment), name="detail"),
]
