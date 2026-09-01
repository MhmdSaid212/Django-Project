from pymongo.collection import Collection

from core.constants import Collections
from core.database import get_collection
from core.soft_delete import SoftDeleteRepositoryMixin, live_query


class CustomerRepository(SoftDeleteRepositoryMixin):
    def __init__(self, collection: Collection | None = None):
        self.collection = collection or get_collection(Collections.CUSTOMERS)

    def find_all(
        self,
        limit: int = 50,
        *,
        query: str | None = None,
        status: str | None = None,
        include_deleted: bool = False,
    ) -> list[dict]:

        filters = {}

        if query:
            filters["$or"] = [
                {"first_name": {"$regex": query, "$options": "i"}},
                {"last_name": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}},
                {"phone": {"$regex": query, "$options": "i"}},
                {"customer_number": {"$regex": query, "$options": "i"}},
            ]

        if status:
            filters["status"] = status

        query_filter = filters if include_deleted else live_query(filters)

        return list(
            self.collection.find(query_filter).limit(limit)
        )

    def find_by_email(self, email: str):
        return self.collection.find_one(
            live_query({
                "email": email.strip().lower()
            })
        )

    def insert_customer(self, document: dict):
        result = self.insert(document)

        return self.collection.find_one({
            "_id": result.inserted_id
        })