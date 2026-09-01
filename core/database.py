from __future__ import annotations

import logging
from typing import Optional

from django.conf import settings
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, PyMongoError, ServerSelectionTimeoutError

from core.exceptions import DatabaseUnavailableError

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        try:
            _client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=4000,
                connectTimeoutMS=4000,
            )
        except PyMongoError as exc:
            logger.exception("Could not create MongoClient")
            raise DatabaseUnavailableError("Could not connect to MongoDB.") from exc
    return _client


def get_database() -> Database:
    return get_client()[settings.MONGODB_DB_NAME]


def get_collection(name: str) -> Collection:
    return get_database()[name]


def ping() -> bool:
    try:
        get_client().admin.command("ping")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError, PyMongoError):
        logger.warning("MongoDB ping failed", exc_info=True)
        return False


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
