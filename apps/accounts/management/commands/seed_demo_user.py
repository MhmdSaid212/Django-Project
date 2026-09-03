from django.conf import settings
from django.core.management.base import BaseCommand

from apps.accounts.repositories import UserRepository
from apps.accounts.services import AuthService
from core.constants import UserRole, UserStatus
from core.exceptions import DatabaseUnavailableError
from core.utils import utcnow


class Command(BaseCommand):
    help = "Seed demo staff users (owner, agent, accountant) for local development."

    def handle(self, *args, **options):
        seeds = [
            (settings.DEMO_OWNER_EMAIL, settings.DEMO_OWNER_PASSWORD, "Owner", "Admin", UserRole.OWNER_ADMIN),
            (settings.DEMO_AGENT_EMAIL, settings.DEMO_AGENT_PASSWORD, "Amina", "Agent", UserRole.TRAVEL_AGENT),
            (
                settings.DEMO_ACCOUNTANT_EMAIL,
                settings.DEMO_ACCOUNTANT_PASSWORD,
                "Karim",
                "Books",
                UserRole.ACCOUNTANT,
            ),
        ]
        try:
            repo = UserRepository()
        except DatabaseUnavailableError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return

        created = 0
        for email, password, first_name, last_name, role in seeds:
            email = email.strip().lower()
            try:
                existing = repo.find_by_email(email)
            except DatabaseUnavailableError as exc:
                self.stderr.write(self.style.ERROR(str(exc)))
                return
            if existing:
                self.stdout.write(self.style.WARNING(f"User already exists: {email}"))
                continue
            now = utcnow()
            repo.insert(
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "password_hash": AuthService.hash_password(password),
                    "role": role.value,
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
            created += 1
            self.stdout.write(self.style.SUCCESS(f"Created {email} / {password} ({role.value})"))

        if created:
            self.stdout.write("Change these passwords before sharing the environment.")
