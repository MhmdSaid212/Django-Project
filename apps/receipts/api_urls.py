from django.urls import path

from apps.receipts import api
from core.http import method_view

app_name = "receipts_api"

urlpatterns = [
    path("<str:id>/", method_view(GET=api.get_receipt), name="detail"),
]
