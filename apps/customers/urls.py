from django.urls import path

from apps.customers import views

app_name = "customers"

urlpatterns = [
    path("", views.customer_list, name="list"),
    path("search/", views.customer_search, name="search"),
    path("create/", views.customer_create, name="create"),
    path("<str:id>/", views.customer_detail, name="detail"),
    path("<str:id>/edit/", views.customer_edit, name="edit"),
    path("<str:id>/attachments/<str:attachment_id>/delete/",views.customer_attachment_delete,name="attachment_delete",  ),
]
