from django.urls import path

from apps.reports import api
from core.http import method_view

app_name = "reports_api"

urlpatterns = [
    path("revenue/", method_view(GET=api.revenue), name="revenue"),
    path("expenses/", method_view(GET=api.expenses), name="expenses"),
    path("payments/", method_view(GET=api.payments), name="payments"),
    path("refunds/", method_view(GET=api.refunds), name="refunds"),
    path("receivables/", method_view(GET=api.receivables), name="receivables"),
    path("payables/", method_view(GET=api.payables), name="payables"),
    path("tour-profitability/", method_view(GET=api.tour_profitability), name="tour_profitability"),
    path("profit-loss/", method_view(GET=api.profit_loss), name="profit_loss"),
    path("transactions/", method_view(GET=api.transactions), name="transactions"),
]
