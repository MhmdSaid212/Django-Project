import json

from django.conf import settings
from django.urls import reverse

from apps.accounts.repositories import UserRepository
from apps.accounts.services import AuthService, UserService
from core.constants import UserRole, UserStatus
from core.exceptions import ValidationError


def _create_user(**overrides):
    payload = {
        "first_name": "Owner",
        "last_name": "Admin",
        "email": "owner@tourops.local",
        "password": "changeme1",
        "role": UserRole.OWNER_ADMIN.value,
        "phone": None,
    }
    payload.update(overrides)
    return UserService().create_user(**payload)


def test_authenticate_accepts_valid_credentials():
    created = _create_user()
    user = AuthService().authenticate("owner@tourops.local", "changeme1")
    assert user["_id"] == created["_id"]
    assert user["email"] == "owner@tourops.local"


def test_authenticate_rejects_bad_password():
    _create_user()
    try:
        AuthService().authenticate("owner@tourops.local", "wrong-password")
    except ValidationError as exc:
        assert "Invalid email or password" in exc.message
    else:
        raise AssertionError("expected ValidationError")


def test_authenticate_rejects_inactive_user():
    created = _create_user(email="agent@tourops.local", role=UserRole.TRAVEL_AGENT.value)
    owner = _create_user()
    UserService().set_status(created["_id"], UserStatus.INACTIVE.value, actor_id=owner["_id"])
    try:
        AuthService().authenticate("agent@tourops.local", "changeme1")
    except Exception as exc:
        assert "inactive" in str(exc).lower()
    else:
        raise AssertionError("expected inactive rejection")


def test_create_user_rejects_duplicate_email():
    _create_user()
    try:
        _create_user()
    except ValidationError as exc:
        assert "already exists" in exc.message
    else:
        raise AssertionError("expected ValidationError")


def test_cannot_deactivate_self():
    owner = _create_user()
    try:
        UserService().set_status(owner["_id"], UserStatus.INACTIVE.value, actor_id=owner["_id"])
    except ValidationError as exc:
        assert "own account" in exc.message
    else:
        raise AssertionError("expected ValidationError")


def test_cannot_deactivate_last_owner():
    owner = _create_user()
    agent = _create_user(
        first_name="Amina",
        last_name="Agent",
        email="agent@tourops.local",
        role=UserRole.TRAVEL_AGENT.value,
    )
    try:
        UserService().set_status(owner["_id"], UserStatus.INACTIVE.value, actor_id=agent["_id"])
    except ValidationError as exc:
        assert "last Owner" in exc.message
    else:
        raise AssertionError("expected ValidationError")


def test_password_is_hashed():
    user = _create_user()
    stored = UserRepository().find_by_id(user["_id"])
    assert stored["password_hash"] != "changeme1"
    assert "pbkdf2" in stored["password_hash"]


def test_login_page_and_success(client):
    _create_user()
    response = client.get(reverse("accounts:login"))
    assert response.status_code == 200
    assert b"Welcome back" in response.content
    assert b"Forgot password?" in response.content
    response = client.post(
        reverse("accounts:login"),
        {"email": "owner@tourops.local", "password": "changeme1"},
    )
    assert response.status_code == 302
    assert reverse("dashboard:owner") in response["Location"]


def test_password_reset_page_and_success(client):
    _create_user()
    response = client.get(reverse("accounts:password_reset"))
    assert response.status_code == 200
    assert b"Reset password" in response.content
    response = client.post(
        reverse("accounts:password_reset"),
        {
            "email": "owner@tourops.local",
            "new_password": "newpass99",
            "confirm_password": "newpass99",
        },
    )
    assert response.status_code == 302
    assert reverse("accounts:login") in response["Location"]
    user = AuthService().authenticate("owner@tourops.local", "newpass99")
    assert user["email"] == "owner@tourops.local"


def test_api_password_reset(client):
    _create_user()
    response = client.post(
        "/api/auth/password/reset/",
        data=json.dumps({"email": "owner@tourops.local", "password": "apireset99"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    user = AuthService().authenticate("owner@tourops.local", "apireset99")
    assert user["email"] == "owner@tourops.local"


def test_login_rejects_open_redirect(client):
    _create_user()
    response = client.post(
        reverse("accounts:login") + "?next=https://evil.example/phish",
        {"email": "owner@tourops.local", "password": "changeme1"},
    )
    assert response.status_code == 302
    assert "evil.example" not in response["Location"]
    assert reverse("dashboard:owner") in response["Location"]


def test_agent_cannot_open_invoices(agent_session):
    assert agent_session.get(reverse("invoices:list")).status_code == 403


def test_accountant_cannot_open_customers(accountant_session):
    assert accountant_session.get(reverse("customers:list")).status_code == 403


def test_agent_can_open_customers(agent_session):
    assert agent_session.get(reverse("customers:list")).status_code == 200


def test_accountant_can_open_invoices(accountant_session):
    assert accountant_session.get(reverse("invoices:list")).status_code == 200


def test_agent_forbidden_from_users(agent_session):
    assert agent_session.get(reverse("accounts:users")).status_code == 403


def test_owner_can_create_user(owner_session):
    response = owner_session.post(
        reverse("accounts:user_create"),
        {
            "first_name": "Nour",
            "last_name": "Saleh",
            "email": "nour@tourops.local",
            "phone": "",
            "role": UserRole.TRAVEL_AGENT.value,
            "password": "secretpass",
            "confirm_password": "secretpass",
        },
    )
    assert response.status_code == 302
    users = UserService().list_users()
    assert any(row["email"] == "nour@tourops.local" for row in users)


def test_logout_post_clears_session(owner_session):
    response = owner_session.post(reverse("accounts:logout"))
    assert response.status_code == 302
    assert reverse("accounts:login") in response["Location"]
    follow = owner_session.get(reverse("customers:list"))
    assert follow.status_code == 302


def test_api_login_and_me(client):
    _create_user()
    response = client.post(
        "/api/auth/login/",
        data=json.dumps({"email": "owner@tourops.local", "password": "changeme1"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["role"] == UserRole.OWNER_ADMIN.value
    me = client.get("/api/auth/me/")
    assert me.status_code == 200
    assert me.json()["data"]["email"] == "owner@tourops.local"


def test_api_agent_forbidden_from_invoices(agent_session):
    response = agent_session.get("/api/invoices/")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_api_accountant_forbidden_from_customers(accountant_session):
    response = accountant_session.get("/api/customers/")
    assert response.status_code == 403


def test_api_owner_lists_customers(owner_session):
    response = owner_session.get("/api/customers/")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_corrupt_session_is_cleared(client):
    session = client.session
    session["tourops_user"] = {"id": "", "email": "x", "role": "HACKER"}
    session.save()
    client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
    response = client.get(reverse("customers:list"))
    assert response.status_code == 302
    assert reverse("accounts:login") in response["Location"]
