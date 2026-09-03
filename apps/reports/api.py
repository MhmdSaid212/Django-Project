from apps.reports.services import ReportService, serialize_report
from core.exceptions import TourOpsError
from core.responses import from_exception, success_response


def _params(request) -> dict:
    return {
        "month": request.GET.get("month") or "",
        "from": request.GET.get("from") or request.GET.get("date_from") or "",
        "to": request.GET.get("to") or request.GET.get("date_to") or "",
        "tour": request.GET.get("tour") or request.GET.get("tour_id") or "",
        "supplier_id": request.GET.get("supplier_id") or "",
        "customer_id": request.GET.get("customer_id") or "",
    }


def _ok(builder):
    def view(request, **kwargs):
        try:
            payload = builder(ReportService(), _params(request))
        except TourOpsError as extra:
            return from_exception(extra)
        return success_response(serialize_report(payload))

    return view


revenue = _ok(lambda service, params: service.revenue(params))
expenses = _ok(lambda service, params: service.expense_breakdown(params))
payments = _ok(lambda service, params: service.payments(params))
refunds = _ok(lambda service, params: service.refunds(params))
receivables = _ok(lambda service, params: service.receivables(params))
payables = _ok(lambda service, params: service.payables(params))
tour_profitability = _ok(lambda service, params: service.tour_profitability(params))
profit_loss = _ok(lambda service, params: service.profit_loss(params))
transactions = _ok(lambda service, params: service.transactions(params))
