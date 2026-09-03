from __future__ import annotations

from django.contrib.auth.hashers import check_password, make_password
from pymongo.errors import DuplicateKeyError

from apps.accounts.constants import ROLE_LABELS
from apps.audit.constants import AuditAction
from apps.audit.services import safe_audit
from apps.accounts.repositories import UserRepository
from apps.accounts.schemas import UserDocument
from apps.accounts.validators import normalize_email, validate_password
from core.constants import UserRole, UserStatus
from core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from core.utils import full_name, utcnow


def present_user(user: dict) -> dict:
    name = full_name(user.get("first_name"), user.get("last_name")) or user.get("email") or "User"
    parts = [part for part in name.split() if part]
    initials = "".join(part[0] for part in parts[:2]).upper() or "U"
    last_login = user.get("last_login_at")
    if last_login and hasattr(last_login, "strftime"):
        last_display = last_login.strftime("%d %b %Y %H:%M")
    elif last_login:
        last_display = str(last_login)
    else:
        last_display = "Never"
    return {
        "id": str(user["_id"]),
        "first_name": user.get("first_name") or "",
        "last_name": user.get("last_name") or "",
        "name": name,
        "initials": initials,
        "email": user.get("email") or "",
        "phone": user.get("phone") or "",
        "role": user.get("role"),
        "role_label": ROLE_LABELS.get(user.get("role"), user.get("role") or ""),
        "status": user.get("status"),
        "last": last_display,
        "last_login_at": last_login,
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }


class AuthService:
    def __init__(self, repository: UserRepository | None = None):
        self.repository = repository or UserRepository()

    def authenticate(self, email: str, password: str) -> dict:
        if not email or not password:
            raise ValidationError("Email and password are required.")

        user = self.repository.find_by_email(normalize_email(email))
        if not user or not check_password(password, user.get("password_hash", "")):
            raise ValidationError("Invalid email or password.")
        if user.get("status") != UserStatus.ACTIVE.value:
            raise PermissionDeniedError("This account is inactive.")

        self.repository.update_last_login(user["_id"], utcnow())
        safe_audit(
            actor_id=user["_id"],
            action=AuditAction.LOGIN.value,
            entity_type="users",
            entity_id=user["_id"],
            description="Signed in.",
        )
        return user

    def change_password(self, user_id, current_password: str, new_password: str) -> dict:
        user = self._require_user(user_id)
        if not check_password(current_password or "", user.get("password_hash", "")):
            raise ValidationError("Current password is incorrect.")
        validate_password(new_password)
        if check_password(new_password, user.get("password_hash", "")):
            raise ValidationError("New password must be different from the current password.")
        self.repository.update(
            user["_id"],
            {"password_hash": self.hash_password(new_password), "updated_at": utcnow()},
        )
        return self._require_user(user["_id"])

    def reset_password_by_email(self, email: str, new_password: str) -> dict:
        """Self-service staff reset by email (no mailer yet). Unknown emails raise a generic error."""
        user = self.repository.find_by_email(normalize_email(email))
        if not user:
            raise ValidationError("No active staff account found for that email.")
        if user.get("status") != UserStatus.ACTIVE.value:
            raise PermissionDeniedError("This account is inactive.")
        validate_password(new_password)
        if check_password(new_password, user.get("password_hash", "")):
            raise ValidationError("New password must be different from the current password.")
        self.repository.update(
            user["_id"],
            {"password_hash": self.hash_password(new_password), "updated_at": utcnow()},
        )
        return self._require_user(user["_id"])

    @staticmethod
    def hash_password(raw_password: str) -> str:
        return make_password(raw_password)

    def _require_user(self, user_id) -> dict:
        user = self.repository.find_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")
        return user


class UserService:
    def __init__(self, repository: UserRepository | None = None):
        self.repository = repository or UserRepository()

    def list_users(self) -> list[dict]:
        return [present_user(user) for user in self.repository.list_users()]

    def get_user(self, user_id) -> dict:
        try:
            user = self.repository.find_by_id(user_id)
        except ValidationError:
            raise NotFoundError("User not found.")
        if not user:
            raise NotFoundError("User not found.")
        return user

    def get_presented(self, user_id) -> dict:
        return present_user(self.get_user(user_id))

    def create_user(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        role: str,
        phone: str | None = None,
        actor_id=None,
    ) -> dict:
        first_name = (first_name or "").strip()
        last_name = (last_name or "").strip()
        email = normalize_email(email)
        phone = (phone or "").strip() or None
        if not first_name or not last_name:
            raise ValidationError("First name and last name are required.")
        if not email:
            raise ValidationError("Email is required.")
        if role not in UserDocument.ALLOWED_ROLES:
            raise ValidationError("Invalid role.")
        validate_password(password)
        if self.repository.find_by_email(email):
            raise ValidationError("A user with this email already exists.")

        now = utcnow()
        document = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password_hash": AuthService.hash_password(password),
            "role": role,
            "phone": phone,
            "status": UserStatus.ACTIVE.value,
            "last_login_at": None,
            "created_at": now,
            "updated_at": now,
        }
        try:
            result = self.repository.insert(document)
        except DuplicateKeyError as exc:
            raise ValidationError("A user with this email already exists.") from exc
        document["_id"] = result.inserted_id
        safe_audit(
            actor_id=actor_id or document["_id"],
            action=AuditAction.CREATED.value,
            entity_type="users",
            entity_id=document["_id"],
            description=f"Created staff user {email} ({role}).",
            after={"email": email, "role": role},
        )
        return document

    def set_status(self, user_id, status: str, *, actor_id) -> dict:
        if status not in UserDocument.ALLOWED_STATUSES:
            raise ValidationError("Invalid status.")
        user = self.get_user(user_id)
        if str(user["_id"]) == str(actor_id) and status != UserStatus.ACTIVE.value:
            raise ValidationError("You cannot deactivate your own account.")
        if (
            user.get("role") == UserRole.OWNER_ADMIN.value
            and status != UserStatus.ACTIVE.value
            and self.repository.count_active_owners(exclude_id=user["_id"]) < 1
        ):
            raise ValidationError("Cannot deactivate the last Owner / Admin.")
        self.repository.update(user["_id"], {"status": status, "updated_at": utcnow()})
        saved = self.get_user(user["_id"])
        safe_audit(
            actor_id=actor_id,
            action=AuditAction.STATUS_CHANGED.value,
            entity_type="users",
            entity_id=saved["_id"],
            description=f"Changed status for {saved.get('email')} to {status}.",
            before={"status": user.get("status")},
            after={"status": status},
        )
        return saved

    def change_role(self, user_id, role: str, *, actor_id) -> dict:
        if role not in UserDocument.ALLOWED_ROLES:
            raise ValidationError("Invalid role.")
        user = self.get_user(user_id)
        if str(user["_id"]) == str(actor_id):
            raise ValidationError("You cannot change your own role.")
        if (
            user.get("role") == UserRole.OWNER_ADMIN.value
            and role != UserRole.OWNER_ADMIN.value
            and self.repository.count_active_owners(exclude_id=user["_id"]) < 1
        ):
            raise ValidationError("Cannot change the role of the last Owner / Admin.")
        self.repository.update(user["_id"], {"role": role, "updated_at": utcnow()})
        saved = self.get_user(user["_id"])
        safe_audit(
            actor_id=actor_id,
            action=AuditAction.ROLE_CHANGED.value,
            entity_type="users",
            entity_id=saved["_id"],
            description=f"Changed role for {saved.get('email')} to {role}.",
            before={"role": user.get("role")},
            after={"role": role},
        )
        return saved

    def reset_password(self, user_id, new_password: str, *, actor_id) -> dict:
        user = self.get_user(user_id)
        if str(user["_id"]) == str(actor_id):
            raise ValidationError("Use the change password form for your own account.")
        validate_password(new_password)
        self.repository.update(
            user["_id"],
            {"password_hash": AuthService.hash_password(new_password), "updated_at": utcnow()},
        )
        return self.get_user(user["_id"])
