from django.urls import path

from apps.invoices import views

app_name = "invoices"

urlpatterns = [
    path("", views.invoice_list, name="list"),
    path("<str:id>/", views.invoice_detail, name="detail"),
    path("<str:id>/print/", views.invoice_print, name="print"),
]
