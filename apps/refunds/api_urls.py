from django.urls import path

from apps.refunds import api
from core.http import method_view

app_name = "refunds_api"

urlpatterns = [
    path("", method_view(GET=api.list_refunds, POST=api.create_refund), name="collection"),
    path("<str:id>/", method_view(GET=api.get_refund), name="detail"),
]
