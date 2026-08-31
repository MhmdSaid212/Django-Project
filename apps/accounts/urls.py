from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("users/", views.users_list, name="users"),
    path("users/<str:id>/", views.user_detail, name="user_detail"),
    path("settings/", views.settings_page, name="settings"),
]
