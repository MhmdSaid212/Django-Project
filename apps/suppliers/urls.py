from django.urls import path

from apps.suppliers import views

app_name = "suppliers"

urlpatterns = [
    path("", views.supplier_list, name="list"),
    path("create/", views.supplier_create, name="create"),
    path("hotels/", views.hotels, name="hotels"),
    path("transportation/", views.transportation, name="transportation"),
    path("tour-guides/", views.tour_guides, name="tour_guides"),
    path("other/", views.other_suppliers, name="other"),
    path("<str:id>/", views.supplier_detail, name="detail"),
    path("<str:id>/edit/", views.supplier_edit, name="edit"),
]
