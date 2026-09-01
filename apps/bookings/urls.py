from django.urls import path

from apps.bookings import views

app_name = "bookings"

urlpatterns = [
    path("", views.booking_list, name="list"),
    path("create/", views.booking_create, name="create"),
    path("<str:id>/", views.booking_detail, name="detail"),
]
