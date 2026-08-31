import json

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts.services import AuthService, UserService, present_user
from core.access import OWNER_ROLES
from core.exceptions import TourOpsError, ValidationError
from core.http import method_view
from core.permissions import clear_session_user, get_session_user, set_session_user
from core.responses import from_exception, success_response


def _json_body(request) -> dict:
    if not request.body:
        return {}
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError as exc:
        raise ValidationError("Invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ValidationError("JSON object required.")
    return payload


@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    try:
        payload = _json_body(request)
        user = AuthService().authenticate(payload.get("email") or "", payload.get("password") or "")
    except TourOpsError as exc:
        return from_exception(exc)
    set_session_user(request, user)
    return success_response(present_user(user))


@csrf_exempt
@require_POST
def logout(request):
    clear_session_user(request)
    return success_response({"signed_out": True})


def me(request):
    session_user = get_session_user(request)
    try:
        return success_response(UserService().get_presented(session_user["id"]))
    except TourOpsError:
        return success_response(session_user)


def list_users(request, **kwargs):
    return success_response({"users": UserService().list_users()})


def create_user(request, **kwargs):
    try:
        payload = _json_body(request)
        user = UserService().create_user(
            first_name=payload.get("first_name") or "",
            last_name=payload.get("last_name") or "",
            email=payload.get("email") or "",
            password=payload.get("password") or "",
            role=payload.get("role") or "",
            phone=payload.get("phone"),
        )
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response(present_user(user), status=201)


def get_user(request, **kwargs):
    try:
        user = UserService().get_presented(kwargs.get("id"))
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response(user)


def set_status(request, **kwargs):
    try:
        payload = _json_body(request)
        user = UserService().set_status(
            kwargs.get("id"),
            payload.get("status") or "",
            actor_id=get_session_user(request)["id"],
        )
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response(present_user(user))


def change_role(request, **kwargs):
    try:
        payload = _json_body(request)
        user = UserService().change_role(
            kwargs.get("id"),
            payload.get("role") or "",
            actor_id=get_session_user(request)["id"],
        )
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response(present_user(user))


def reset_password(request, **kwargs):
    try:
        payload = _json_body(request)
        user = UserService().reset_password(
            kwargs.get("id"),
            payload.get("password") or "",
            actor_id=get_session_user(request)["id"],
        )
    except TourOpsError as exc:
        return from_exception(exc)
    return success_response(present_user(user))


users_collection = method_view(*OWNER_ROLES, GET=list_users, POST=create_user)
users_detail = method_view(*OWNER_ROLES, GET=get_user)
users_status = method_view(*OWNER_ROLES, POST=set_status)
users_role = method_view(*OWNER_ROLES, POST=change_role)
users_password = method_view(*OWNER_ROLES, POST=reset_password)
me_view = method_view(GET=me)
