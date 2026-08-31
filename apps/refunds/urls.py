from django.urls import path

from apps.refunds import views

app_name = "refunds"

urlpatterns = [
    path("", views.refund_list, name="list"),
    path("<str:id>/", views.refund_detail, name="detail"),
]
