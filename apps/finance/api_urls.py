from django.urls import path

from apps.finance import api
from core.http import method_view

app_name = "finance_api"

urlpatterns = [
    path("receivables/", method_view(GET=api.receivables), name="receivables"),
    path("payables/", method_view(GET=api.payables), name="payables"),
]
