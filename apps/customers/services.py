from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from core.constants import Collections
from core.numbering import next_number
from core.utils import utcnow

from apps.customers.repositories import CustomerRepository


class CustomerService:
    def __init__(self, repository: CustomerRepository | None = None):
        self.repository = repository or CustomerRepository()


    def _validate_customer_data(self, data: dict, date_of_birth=None):
            first_name = data.get("first_name", "").strip()
            last_name = data.get("last_name", "").strip()
            email = data.get("email", "").strip()
            phone = data.get("phone", "").strip()

            # Required fields
            if not first_name: 
                raise ValueError("First name is required.")

            if not last_name:
                raise ValueError("Last name is required.")

            if not email:
                raise ValueError("Email is required.")

            if not phone:
                raise ValueError("Phone number is required.")

            # Names: letters, spaces, hyphens and apostrophes only
            name_pattern = r"^[A-Za-zÀ-ÖØ-öø-ÿ' -]+$"

            import re

            if not re.fullmatch(name_pattern, first_name):
                raise ValueError(
                    "First name can only contain letters, spaces, hyphens, and apostrophes."
                )

            if not re.fullmatch(name_pattern, last_name):
                raise ValueError(
                    "Last name can only contain letters, spaces, hyphens, and apostrophes."
                )

            # Email
            try:
                validate_email(email)
            except ValidationError:
                raise ValueError("Please enter a valid email address.")

            # Date of birth
            if date_of_birth:
                if isinstance(date_of_birth, datetime):
                    birth_date = date_of_birth.date()
                elif isinstance(date_of_birth, date):
                    birth_date = date_of_birth
                else:
                    raise ValueError("Invalid date of birth.")

                if birth_date > date.today():
                    raise ValueError("Date of birth cannot be in the future.")

            # Passport
            passport = data.get("passport") or {}
            passport_expiry = passport.get("expiry_date")

            if passport_expiry:
                try:
                    expiry = date.fromisoformat(str(passport_expiry))
                except ValueError:
                    raise ValueError("Please enter a valid passport expiry date.")

                if expiry < date.today():
                    raise ValueError("Passport expiry date cannot be in the past.")

            # Emergency contact name
            emergency = data.get("emergency_contact") or {}
            emergency_name = (emergency.get("name") or "").strip()

            if emergency_name and not re.fullmatch(name_pattern, emergency_name):
                raise ValueError(
                    "Emergency contact name can only contain letters, spaces, hyphens, and apostrophes."
                )

    def list_items(
        self,
        query: str | None = None,
        status: str | None = None,
        include_deleted: bool = False,
    ):
        return self.repository.find_all(
            query=query,
            status=status,
            include_deleted=include_deleted,
        )

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)

    def create(self, data: dict, date_of_birth=None, user=None):

        self._validate_customer_data(data, date_of_birth)

        email = data["email"].strip().lower()

        # Duplicate active customer check
        existing = self.repository.find_by_email(email)

        if existing:
            raise ValueError(
                "A customer with this email already exists."
            )

        now = utcnow()

        user_id = None

        if user and user.get("id"):
            from bson import ObjectId
            user_id = ObjectId(user["id"])

        customer = {
            "customer_number": next_number(Collections.CUSTOMERS),

            "first_name": data["first_name"].strip(),
            "last_name": data["last_name"].strip(),
            "email": email,
            "phone": data["phone"].strip(),

            "date_of_birth": date_of_birth,
            "nationality": data.get("nationality"),

            "address": data.get("address", {
                "country": "",
                "city": "",
                "street": None,
            }),

            "passport": data.get("passport", {
                "number": None,
                "expiry_date": None,
                "issuing_country": None,
            }),

            "emergency_contact": data.get(
                "emergency_contact",
                {
                    "name": None,
                    "phone": None,
                    "relationship": None,
                },
            ),

            "notes": data.get("notes"),

            "status": "ACTIVE",
            "created_by": user_id,
            "created_at": now,
            "updated_at": now,
        }

        return self.repository.insert_customer(customer)

    def update(self, doc_id: str, data: dict, user=None):
        customer = self.repository.find_by_id(doc_id)

        if not customer:
            return None

        # Check email uniqueness if email is being changed
        if "email" in data:
            email = data["email"].strip().lower()

            if email != customer.get("email"):
                existing = self.repository.find_by_email(email)

                if existing and str(existing["_id"]) != str(customer["_id"]):
                    raise ValueError(
                        "A customer with this email already exists."
                    )

                data["email"] = email

        allowed_fields = [
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
        ]

        updates = {
            field: data[field]
            for field in allowed_fields
            if field in data
        }

        if updates:
            updates["updated_at"] = utcnow()
            self.repository.update(doc_id, updates)

        return self.repository.find_by_id(doc_id)
