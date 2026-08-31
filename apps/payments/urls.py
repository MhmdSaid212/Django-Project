from django.urls import path

from apps.payments import views

app_name = "payments"

urlpatterns = [
    path("", views.payment_list, name="list"),
    path("<str:id>/", views.payment_detail, name="detail"),
]
