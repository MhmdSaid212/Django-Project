from django.urls import reverse


def test_wireframe_pages_render(owner_session):
    named = [
        ("dashboard:owner", None),
        ("customers:list", None),
        ("customers:create", None),
        ("customers:detail", ["cus-1001"]),
        ("bookings:list", None),
        ("bookings:create", None),
        ("bookings:detail", ["bk-1048"]),
        ("tours:list", None),
        ("tours:create", None),
        ("availability:index", None),
        ("packages:list", None),
        ("packages:create", None),
        ("suppliers:list", None),
        ("suppliers:hotels", None),
        ("suppliers:create", None),
        ("invoices:list", None),
        ("invoices:detail", ["inv-1042"]),
        ("invoices:print", ["inv-1042"]),
        ("payments:list", None),
        ("payments:detail", ["pay-1042"]),
        ("receipts:list", None),
        ("receipts:detail", ["rec-1042"]),
        ("refunds:list", None),
        ("refunds:detail", ["ref-1012"]),
        ("expenses:list", None),
        ("expenses:create", None),
        ("supplier_payments:list", None),
        ("supplier_payments:create", None),
        ("finance:customer_balances", None),
        ("reports:list", None),
        ("reports:profitability", None),
        ("reports:revenue", None),
        ("reports:expenses", None),
        ("reports:profit_loss", None),
        ("notifications:list", None),
        ("audit:list", None),
        ("accounts:users", None),
        ("accounts:user_create", None),
        ("accounts:settings", None),
    ]
    for name, args in named:
        url = reverse(name, args=args) if args else reverse(name)
        response = owner_session.get(url)
        assert response.status_code == 200, f"{name} {url} -> {response.status_code}"
