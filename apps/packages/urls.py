from django.urls import path

from apps.packages import views

app_name = "packages"

urlpatterns = [
    path("", views.package_list, name="list"),
    path("create/", views.package_create, name="create"),
    path("<str:id>/", views.package_detail, name="detail"),
    path("<str:id>/edit/", views.package_edit, name="edit"),
]
