from core.access import ALL_ROLES, role_values
from core.permissions import clear_session_user, get_session_user


class SessionIntegrityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._allowed_roles = role_values(*ALL_ROLES)

    def __call__(self, request):
        user = get_session_user(request)
        if user is not None:
            if not user.get("id") or user.get("role") not in self._allowed_roles:
                clear_session_user(request)
        return self.get_response(request)
