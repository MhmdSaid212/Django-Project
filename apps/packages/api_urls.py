from django.urls import path

from apps.packages import api
from core.http import method_view

app_name = "packages_api"

urlpatterns = [
    path("", method_view(GET=api.list_packages, POST=api.create_package), name="collection"),
    path("<str:id>/", method_view(GET=api.get_package, PATCH=api.patch_package), name="detail"),
]
