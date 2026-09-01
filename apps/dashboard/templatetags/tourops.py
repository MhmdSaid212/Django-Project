from django import template

register = template.Library()

_BADGE = {
    "ACTIVE": "b-ok",
    "AVAILABLE": "b-ok",
    "CONFIRMED": "b-ok",
    "COMPLETED": "b-ok",
    "PAID": "b-ok",
    "APPROVED": "b-ok",
    "PENDING": "b-warn",
    "DRAFT": "b-mute",
    "ISSUED": "b-info",
    "PARTIALLY_PAID": "b-warn",
    "UNPAID": "b-warn",
    "IN_PROGRESS": "b-info",
    "FULLY_BOOKED": "b-warm",
    "INACTIVE": "b-mute",
    "CANCELLED": "b-bad",
    "REJECTED": "b-bad",
    "VOIDED": "b-bad",
    "OVERDUE": "b-bad",
    "REFUNDED": "b-info",
    "HOTEL": "b-warm",
    "TRANSPORTATION": "b-info",
    "TOUR_GUIDE": "b-ok",
    "OWNER_ADMIN": "b-warm",
    "ACCOUNTANT": "b-info",
    "TRAVEL_AGENT": "b-ok",
}


@register.filter
def money(value):
    if value is None or value == "":
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number.is_integer():
        return f"${number:,.0f}"
    return f"${number:,.2f}"


@register.filter
def money_signed(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    sign = "+" if number >= 0 else "−"
    return f"{sign}{money(abs(number))}"


@register.filter
def badge_class(status):
    return _BADGE.get(str(status or "").upper(), "b-mute")


@register.filter
def labelize(value):
    return str(value or "").replace("_", " ").title()


@register.simple_tag(takes_context=True)
def nav_active(context, *namespaces):
    match = getattr(context.get("request"), "resolver_match", None)
    current = getattr(match, "namespace", "")
    return "is-active" if current in namespaces else ""
