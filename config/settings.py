"""
TourOps Django settings.

Architecture decision:
- MongoDB (via PyMongo) is the primary application database.
- Django ORM models.py files are intentionally NOT used for business collections.
- Signed-cookie sessions are used so we do not need a SQL database for login sessions.
  Production teams may later switch to Redis or a MongoDB session backend.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-only-change-me")
DEBUG = _env_bool("DJANGO_DEBUG", "true")
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

# ---------------------------------------------------------------------------
# MongoDB — application database (not Django ORM)
# ---------------------------------------------------------------------------
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "tourops")

INSTALLED_APPS = [
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Feature apps — each team owns a vertical slice. No Django ORM models.
    "apps.accounts",
    "apps.taxes",
    "apps.attachments",
    "apps.customers",
    "apps.bookings",
    "apps.suppliers",
    "apps.tours",
    "apps.packages",
    "apps.invoices",
    "apps.payments",
    "apps.receipts",
    "apps.refunds",
    "apps.expenses",
    "apps.supplier_payments",
    "apps.finance",
    "apps.reports",
    "apps.dashboard",
    "apps.notifications",
    "apps.audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.branding",
                "core.context_processors.current_user",
                "core.context_processors.navigation",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# No SQL DATABASES required for business data.
# Django still expects a default DATABASES key for a few contrib checks;
# we point it at a local sqlite file that is NOT used for TourOps collections.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Sessions: signed cookies so login works without relying on SQLite as a real store.
# The sqlite file above exists only to keep Django happy; do not put business data there.
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 8  # 8 hours

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "accounts:login"

# Demo seed user (development only). Change immediately in any shared environment.
DEMO_OWNER_EMAIL = os.getenv("DEMO_OWNER_EMAIL", "owner@tourops.local")
DEMO_OWNER_PASSWORD = os.getenv("DEMO_OWNER_PASSWORD", "changeme")
