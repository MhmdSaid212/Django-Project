from django.urls import reverse


def test_key_api_routes_reverse():
    assert reverse("customers_api:collection") == "/api/customers/"
    assert reverse("bookings_api:confirm", args=["abc"]) == "/api/bookings/abc/confirm/"
    assert reverse("tours_api:availability", args=["abc"]) == "/api/tours/abc/availability/"
    assert reverse("invoices_api:payments", args=["abc"]) == "/api/invoices/abc/payments/"
    assert reverse("payments_api:receipt", args=["abc"]) == "/api/payments/abc/receipt/"
    assert reverse("finance_api:receivables") == "/api/finance/receivables/"
    assert reverse("reports_api:profit_loss") == "/api/reports/profit-loss/"
    assert reverse("dashboard_api:owner") == "/api/dashboard/owner/"
    assert reverse("accounts_api:login") == "/api/auth/login/"
    assert reverse("accounts_api:me") == "/api/auth/me/"
    assert reverse("accounts_api:password_reset") == "/api/auth/password/reset/"
    assert reverse("accounts_api:users") == "/api/users/"
    assert reverse("suppliers_api:collection") == "/api/suppliers/"
    assert reverse("packages_api:collection") == "/api/packages/"
    assert reverse("tours_api:collection") == "/api/tours/"
    assert reverse("accounts:password_reset") == "/password/reset/"
