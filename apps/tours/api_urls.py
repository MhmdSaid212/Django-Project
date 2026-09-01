from django.urls import path

from apps.expenses.api import expenses_for_tour
from apps.finance.api import tour_profitability
from apps.tours import api
from core.access import FINANCE_ROLES, OPERATIONS_ROLES
from core.http import method_view

app_name = "tours_api"

urlpatterns = [
    path("", method_view(*OPERATIONS_ROLES, GET=api.list_tours, POST=api.create_tour), name="collection"),
    path("<str:id>/availability/", method_view(*OPERATIONS_ROLES, GET=api.tour_availability), name="availability"),
    path("<str:tour_id>/expenses/", method_view(*FINANCE_ROLES, GET=expenses_for_tour), name="expenses"),
    path("<str:tour_id>/profitability/", method_view(*FINANCE_ROLES, GET=tour_profitability), name="profitability"),
    path("<str:id>/", method_view(*OPERATIONS_ROLES, GET=api.get_tour, PATCH=api.patch_tour), name="detail"),
]
