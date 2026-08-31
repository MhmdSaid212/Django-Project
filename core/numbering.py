from __future__ import annotations

from pymongo import ReturnDocument
from pymongo.errors import PyMongoError

from core.constants import NUMBER_PREFIXES, NUMBER_START, Collections
from core.database import get_collection
from core.exceptions import DatabaseUnavailableError


def next_number(collection_name: str, prefix: str | None = None) -> str:
    prefix = prefix or NUMBER_PREFIXES.get(collection_name)
    if not prefix:
        raise ValueError(f"No number prefix configured for collection {collection_name!r}")

    try:
        counters = get_collection(Collections.COUNTERS)
        doc = counters.find_one_and_update(
            {"_id": collection_name},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as exc:
        raise DatabaseUnavailableError("Could not allocate a business number.") from exc

    seq = int(doc["seq"])
    displayed = NUMBER_START + seq - 1
    return f"{prefix}-{displayed}"


def peek_next_number(collection_name: str, prefix: str | None = None) -> str:
    prefix = prefix or NUMBER_PREFIXES.get(collection_name, "DOC")
    try:
        doc = get_collection(Collections.COUNTERS).find_one({"_id": collection_name})
    except PyMongoError:
        doc = None
    seq = int(doc["seq"]) + 1 if doc and "seq" in doc else 1
    displayed = NUMBER_START + seq - 1
    return f"{prefix}-{displayed}"
