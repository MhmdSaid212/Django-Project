"""Create a development Owner/Admin user if one does not exist."""
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.accounts.repositories import UserRepository
from apps.accounts.services import AuthService
from core.constants import UserRole, UserStatus
from core.exceptions import DatabaseUnavailableError
from core.utils import utcnow


class Command(BaseCommand):
    help = "Seed a demo OWNER_ADMIN user for local development."

    def handle(self, *args, **options):
        email = settings.DEMO_OWNER_EMAIL.strip().lower()
        try:
            repo = UserRepository()
            existing = repo.find_by_email(email)
        except DatabaseUnavailableError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return

        if existing:
            self.stdout.write(self.style.WARNING(f"User already exists: {email}"))
            return

        now = utcnow()
        repo.insert(
            {
                "first_name": "Owner",
                "last_name": "Admin",
                "email": email,
                "password_hash": AuthService.hash_password(settings.DEMO_OWNER_PASSWORD),
                "role": UserRole.OWNER_ADMIN.value,
                "phone": None,
                "status": UserStatus.ACTIVE.value,
                "last_login_at": None,
                "is_deleted": False,
                "deleted_at": None,
                "deleted_by": None,
                "created_at": now,
                "updated_at": now,
            }
        )
        self.stdout.write(self.style.SUCCESS(f"Created {email} / {settings.DEMO_OWNER_PASSWORD}"))
        self.stdout.write("Change this password before sharing the environment.")
