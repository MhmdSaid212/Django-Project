from __future__ import annotations

from collections.abc import Callable

from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt

from core.permissions import login_required, role_required
from core.responses import error_response, not_implemented


def method_view(*roles, **handlers: Callable):
    allowed = sorted(handlers)

    def view(request: HttpRequest, *args, **kwargs):
        handler = handlers.get(request.method)
        if handler is None:
            return error_response(
                "METHOD_NOT_ALLOWED",
                f"Allowed methods: {', '.join(allowed)}.",
                status=405,
            )
        return handler(request, *args, **kwargs)

    view.handlers = handlers
    protected = role_required(*roles)(view) if roles else login_required(view)
    return csrf_exempt(protected)


def unimplemented(*methods: str, message: str | None = None, roles: tuple = ()):
    def handler(request, **kwargs):
        return not_implemented(message or f"{request.method} {request.path} is not implemented yet.")

    return method_view(*roles, **{method: handler for method in methods})
