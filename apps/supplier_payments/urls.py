from django.urls import path

from apps.supplier_payments import views

app_name = "supplier_payments"

urlpatterns = [
    path("", views.supplier_payment_list, name="list"),
    path("<str:id>/", views.supplier_payment_detail, name="detail"),
]
