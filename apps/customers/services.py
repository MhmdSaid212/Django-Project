from core.constants import Collections
from core.numbering import next_number
from core.utils import utcnow

from apps.customers.repositories import CustomerRepository


class CustomerService:
    def __init__(self, repository: CustomerRepository | None = None):
        self.repository = repository or CustomerRepository()

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