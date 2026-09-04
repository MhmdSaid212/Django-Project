from __future__ import annotations

import re
from datetime import date, datetime

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from pymongo.errors import DuplicateKeyError, PyMongoError

from apps.customers.repositories import CustomerRepository
from core.constants import Collections, RecordStatus
from core.exceptions import DatabaseUnavailableError, NotFoundError, ValidationError
from core.numbering import next_number
from core.utils import full_name, parse_object_id, utcnow

_NAME_PATTERN = r"^[A-Za-zÀ-ÖØ-öø-ÿ' -]+$"


def _blank(value) -> str | None:
    text = (str(value).strip() if value is not None else "") or None
    return text


def present_customer(document: dict) -> dict:
    first = document.get("first_name") or ""
    last = document.get("last_name") or ""
    name = full_name(first, last) or document.get("email") or "Customer"
    parts = [part for part in (first, last) if part]
    initials = "".join(part[0] for part in parts[:2]).upper() or "C"
    address = document.get("address") or {}
    passport = document.get("passport") or {}
    return {
        "id": str(document["_id"]),
        "number": document.get("customer_number") or "",
        "customer_number": document.get("customer_number") or "",
        "first_name": first,
        "last_name": last,
        "first": first,
        "last": last,
        "name": name,
        "initials": initials,
        "email": document.get("email") or "",
        "phone": document.get("phone") or "",
        "city": address.get("city") or "",
        "country": address.get("country") or "",
        "passport": passport.get("number") or "",
        "nationality": document.get("nationality") or "",
        "status": document.get("status") or RecordStatus.ACTIVE.value,
        "notes": document.get("notes") or "",
        "balance": 0,
        "bookings": 0,
        "upcoming": "",
        "created_at": document.get("created_at"),
        "updated_at": document.get("updated_at"),
    }


class CustomerService:
    def __init__(self, repository: CustomerRepository | None = None):
        self.repository = repository or CustomerRepository()

    def list_items(
        self,
        query: str | None = None,
        status: str | None = None,
        include_deleted: bool = False,
    ) -> list[dict]:
        if query or status or include_deleted:
            return self.repository.find_all(
                limit=500,
                query=query,
                status=status,
                include_deleted=include_deleted,
            )
        return self.repository.list_customers()

    def list_presented(self) -> list[dict]:
        return [present_customer(doc) for doc in self.list_items()]

    def list_options(self) -> list[tuple[str, str]]:
        return [(row["id"], f"{row['name']} · {row['number']}") for row in self.list_presented()]

    def get(self, customer_id) -> dict | None:
        try:
            return self.repository.find_by_id(customer_id)
        except ValidationError:
            return None

    def get_presented(self, customer_id) -> dict:
        document = self.get(customer_id)
        if not document:
            raise NotFoundError("Customer not found.")
        return present_customer(document)

    def _validate_customer_data(self, data: dict, date_of_birth=None) -> None:
        first_name = (data.get("first_name") or "").strip()
        last_name = (data.get("last_name") or "").strip()
        email = (data.get("email") or "").strip()
        phone = (data.get("phone") or "").strip()
        if not first_name:
            raise ValueError("First name is required.")
        if not last_name:
            raise ValueError("Last name is required.")
        if not email:
            raise ValueError("Email is required.")
        if not phone:
            raise ValueError("Phone number is required.")
        if not re.fullmatch(_NAME_PATTERN, first_name):
            raise ValueError("First name can only contain letters, spaces, hyphens, and apostrophes.")
        if not re.fullmatch(_NAME_PATTERN, last_name):
            raise ValueError("Last name can only contain letters, spaces, hyphens, and apostrophes.")
        try:
            validate_email(email)
        except DjangoValidationError as extra:
            raise ValueError("Please enter a valid email address.") from extra
        if date_of_birth:
            if isinstance(date_of_birth, datetime):
                birth_date = date_of_birth.date()
            elif isinstance(date_of_birth, date):
                birth_date = date_of_birth
            else:
                raise ValueError("Invalid date of birth.")
            if birth_date > date.today():
                raise ValueError("Date of birth cannot be in the future.")
        passport = data.get("passport") or {}
        passport_expiry = passport.get("expiry_date")
        if passport_expiry:
            try:
                expiry = date.fromisoformat(str(passport_expiry)[:10])
            except ValueError as extra:
                raise ValueError("Please enter a valid passport expiry date.") from extra
            if expiry < date.today():
                raise ValueError("Passport expiry date cannot be in the past.")
        emergency_name = ((data.get("emergency_contact") or {}).get("name") or "").strip()
        if emergency_name and not re.fullmatch(_NAME_PATTERN, emergency_name):
            raise ValueError("Emergency contact name can only contain letters, spaces, hyphens, and apostrophes.")

    def create(
        self,
        data=None,
        date_of_birth=None,
        user=None,
        *,
        actor_id=None,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        phone: str = "",
        **fields,
    ) -> dict:
        if isinstance(data, dict):
            return self._create_from_form(data, date_of_birth=date_of_birth, user=user)
        return self._create_from_fields(
            actor_id=actor_id,
            first_name=first_name or "",
            last_name=last_name or "",
            email=email or "",
            phone=phone,
            **fields,
        )

    def _create_from_form(self, data: dict, date_of_birth=None, user=None) -> dict:
        self._validate_customer_data(data, date_of_birth)
        email = data["email"].strip().lower()
        existing = self.repository.find_by_email(email)
        if existing:
            raise ValueError("A customer with this email already exists.")
        now = utcnow()
        user_id = None
        if user and user.get("id"):
            user_id = parse_object_id(user["id"], field="created_by")
        address = data.get("address") if isinstance(data.get("address"), dict) else {}
        passport = data.get("passport") if isinstance(data.get("passport"), dict) else {}
        emergency = data.get("emergency_contact") if isinstance(data.get("emergency_contact"), dict) else {}
        document = {
            "customer_number": next_number(Collections.CUSTOMERS),
            "first_name": data["first_name"].strip(),
            "last_name": data["last_name"].strip(),
            "email": email,
            "phone": data["phone"].strip(),
            "date_of_birth": date_of_birth,
            "nationality": data.get("nationality"),
            "address": {
                "country": address.get("country") or "",
                "city": address.get("city") or "",
                "street": address.get("street"),
            },
            "passport": {
                "number": passport.get("number"),
                "expiry_date": passport.get("expiry_date"),
                "issuing_country": passport.get("issuing_country"),
            },
            "emergency_contact": {
                "name": emergency.get("name"),
                "phone": emergency.get("phone"),
                "relationship": emergency.get("relationship"),
            },
            "notes": data.get("notes"),
            "status": "ACTIVE",
            "created_by": user_id,
            "created_at": now,
            "updated_at": now,
        }
        try:
            result = self.repository.insert(document)
        except DuplicateKeyError as extra:
            raise ValueError("A customer with this email already exists.") from extra
        except PyMongoError as extra:
            raise DatabaseUnavailableError("Could not save the customer.") from extra
        document["_id"] = result.inserted_id
        return self.repository.find_by_id(document["_id"])

    def _create_from_fields(
        self,
        *,
        actor_id,
        first_name: str,
        last_name: str,
        email: str,
        phone: str = "",
        **fields,
    ) -> dict:
        first = (first_name or "").strip()
        last = (last_name or "").strip()
        if not first or not last:
            raise ValidationError("First and last name are required.")
        email = (email or "").strip().lower()
        if not email or "@" not in email:
            raise ValidationError("A valid email is required.")
        now = utcnow()
        document = {
            "customer_number": next_number(Collections.CUSTOMERS),
            "first_name": first,
            "last_name": last,
            "email": email,
            "phone": (phone or "").strip(),
            "nationality": _blank(fields.get("nationality")),
            "address": {
                "city": (fields.get("city") or "").strip(),
                "country": (fields.get("country") or "").strip(),
                "street": _blank(fields.get("street")),
            },
            "passport": {"number": _blank(fields.get("passport") or fields.get("passport_number"))},
            "notes": _blank(fields.get("notes")),
            "status": RecordStatus.ACTIVE.value,
            "created_by": parse_object_id(actor_id, field="created_by"),
            "created_at": now,
            "updated_at": now,
        }
        try:
            result = self.repository.insert(document)
        except DuplicateKeyError as extra:
            raise ValidationError("A customer with this email already exists.") from extra
        except PyMongoError as extra:
            raise DatabaseUnavailableError("Could not save the customer.") from extra
        document["_id"] = result.inserted_id
        found = self.get(document["_id"])
        if not found:
            raise DatabaseUnavailableError("Could not save the customer.")
        return found

    def update(self, doc_id: str, data: dict, user=None) -> dict | None:
        customer = self.get(doc_id)
        if not customer:
            return None
        payload = dict(data)
        date_of_birth = payload.get("date_of_birth")
        self._validate_customer_data(payload, date_of_birth)
        if "email" in payload:
            email = payload["email"].strip().lower()
            if email != customer.get("email"):
                existing = self.repository.find_by_email(email)
                if existing and str(existing["_id"]) != str(customer["_id"]):
                    raise ValueError("A customer with this email already exists.")
            payload["email"] = email
        allowed_fields = {
            "first_name",
            "last_name",
            "email",
            "phone",
            "date_of_birth",
            "nationality",
            "address",
            "passport",
            "emergency_contact",
            "notes",
            "status",
        }
        updates = {field: payload[field] for field in allowed_fields if field in payload}
        if user and user.get("id"):
            updates["updated_by"] = parse_object_id(user["id"], field="updated_by")
        updates["updated_at"] = utcnow()
        try:
            self.repository.update(doc_id, updates)
        except PyMongoError as extra:
            raise DatabaseUnavailableError("Could not save the customer.") from extra
        return self.get(doc_id)
