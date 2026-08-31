"""Tiny HTTP helpers so one URL can accept GET and POST without duplicate path() entries."""
from __future__ import annotations

from collections.abc import Callable

from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt

from core.permissions import login_required
from core.responses import error_response, not_implemented


def method_view(**handlers: Callable):
    """
    Route one URL to different placeholder (or real) callables by HTTP method.

    Django matches path() in order and ignores HTTP method, so two path("", ...)
    entries would hide the second one. Use this instead.
    """

    allowed = sorted(handlers)

    @csrf_exempt  # JSON APIs will send a CSRF token later; skeleton uses method-based 501s.
    @login_required
    def view(request: HttpRequest, *args, **kwargs):
        handler = handlers.get(request.method)
        if handler is None:
            return error_response(
                "METHOD_NOT_ALLOWED",
                f"Allowed methods: {', '.join(allowed)}.",
                status=405,
            )
        return handler(request, *args, **kwargs)

    view.handlers = handlers  # type: ignore[attr-defined]
    return view


def unimplemented(*methods: str, message: str | None = None):
    """Shortcut: any of the given methods returns the same 501 placeholder."""

    def handler(request, **kwargs):
        return not_implemented(message or f"{request.method} {request.path} is not implemented yet.")

    return method_view(**{method: handler for method in methods})
