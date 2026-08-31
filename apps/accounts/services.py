"""Authentication rules. Views stay thin."""
from __future__ import annotations

from django.contrib.auth.hashers import check_password, make_password

from apps.accounts.repositories import UserRepository
from core.constants import UserStatus
from core.exceptions import PermissionDeniedError, ValidationError
from core.utils import utcnow


class AuthService:
    def __init__(self, repository: UserRepository | None = None):
        self.repository = repository or UserRepository()

    def authenticate(self, email: str, password: str) -> dict:
        if not email or not password:
            raise ValidationError("Email and password are required.")

        user = self.repository.find_by_email(email)
        if not user or not check_password(password, user.get("password_hash", "")):
            raise ValidationError("Invalid email or password.")
        if user.get("status") != UserStatus.ACTIVE.value:
            raise PermissionDeniedError("This account is inactive.")

        self.repository.update_last_login(user["_id"], utcnow())
        return user

    @staticmethod
    def hash_password(raw_password: str) -> str:
        return make_password(raw_password)
