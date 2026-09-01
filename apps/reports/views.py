from django.contrib import messages
from django.shortcuts import render

from apps.reports.forms import ReportFilterForm
from apps.reports.services import ReportService
from core.access import REPORT_ROLES
from core.exceptions import DatabaseUnavailableError, TourOpsError
from core.permissions import login_required, role_required


def _params(request) -> dict:
    return {
        "month": request.GET.get("month") or "",
        "from": request.GET.get("from") or request.GET.get("date_from") or "",
        "to": request.GET.get("to") or request.GET.get("date_to") or "",
        "tour": request.GET.get("tour") or request.GET.get("tour_id") or "",
    }


def _query(params: dict) -> str:
    parts = []
    if params.get("month"):
        parts.append(f"month={params['month']}")
    if params.get("from"):
        parts.append(f"from={params['from']}")
    if params.get("to"):
        parts.append(f"to={params['to']}")
    if params.get("tour"):
        parts.append(f"tour={params['tour']}")
    return ("?" + "&".join(parts)) if parts else ""


def _context(request, *, title, heading, extra=None):
    service = ReportService()
    params = _params(request)
    try:
        tours = service.tour_options()
    except DatabaseUnavailableError:
        messages.error(request, "Cannot reach MongoDB. Reports are unavailable.")
        tours = []
    form = ReportFilterForm(
        initial={
            "month": params["month"],
            "date_from": params["from"] or None,
            "date_to": params["to"] or None,
            "tour_id": params["tour"],
        },
        tour_choices=tours,
    )
    payload = {
        "page_title": title,
        "page_heading": heading,
        "form": form,
        "filters": params,
        "query": _query(params),
        "tour_choices": tours,
    }
    if extra:
        payload.update(extra)
    return payload


@login_required
@role_required(*REPORT_ROLES)
def report_list(request):
    ctx = _context(request, title="Reports", heading="Financial reports")
    return render(request, "reports/list.html", ctx)


@login_required
@role_required(*REPORT_ROLES)
def report_revenue(request):
    service = ReportService()
    params = _params(request)
    try:
        report = service.revenue(params)
    except DatabaseUnavailableError:
        messages.error(request, "Cannot reach MongoDB. Reports are unavailable.")
        report = None
    except TourOpsError as extra:
        messages.error(request, extra.message)
        report = None
    ctx = _context(request, title="Revenue vs cost", heading="Revenue vs cost", extra={"report": report})
    return render(request, "reports/revenue.html", ctx)


@login_required
@role_required(*REPORT_ROLES)
def report_expenses(request):
    service = ReportService()
    params = _params(request)
    try:
        report = service.expense_breakdown(params)
    except DatabaseUnavailableError:
        messages.error(request, "Cannot reach MongoDB. Reports are unavailable.")
        report = None
    except TourOpsError as extra:
        messages.error(request, extra.message)
        report = None
    ctx = _context(request, title="Expense breakdown", heading="Expense breakdown", extra={"report": report})
    return render(request, "reports/expenses.html", ctx)


@login_required
@role_required(*REPORT_ROLES)
def report_profit_loss(request):
    service = ReportService()
    params = _params(request)
    try:
        report = service.profit_loss(params)
    except DatabaseUnavailableError:
        messages.error(request, "Cannot reach MongoDB. Reports are unavailable.")
        report = None
    except TourOpsError as extra:
        messages.error(request, extra.message)
        report = None
    ctx = _context(request, title="Cash flow", heading="Cash flow", extra={"report": report})
    return render(request, "reports/profit_loss.html", ctx)


@login_required
@role_required(*REPORT_ROLES)
def tour_profitability(request):
    service = ReportService()
    params = _params(request)
    try:
        report = service.tour_profitability(params)
    except DatabaseUnavailableError:
        messages.error(request, "Cannot reach MongoDB. Reports are unavailable.")
        report = None
    except TourOpsError as extra:
        messages.error(request, extra.message)
        report = None
    selected = (report or {}).get("selected") if report else None
    ctx = _context(
        request,
        title="Tour profitability",
        heading="Tour profitability",
        extra={"report": report, "selected": selected},
    )
    return render(request, "reports/profitability.html", ctx)
