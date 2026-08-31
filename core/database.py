"""
Reusable MongoDB client for TourOps.

Decision: one MongoClient per process, not per request.
PyMongo's MongoClient is a thread-safe connection pool.
Creating a new client on every view would leak sockets and slow the app down.
"""
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
    """Return the process-wide MongoClient, creating it on first use."""
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
    """Return the TourOps database (name from MONGODB_DB_NAME)."""
    return get_client()[settings.MONGODB_DB_NAME]


def get_collection(name: str) -> Collection:
    """Return a named collection. Use core.constants.Collections values."""
    return get_database()[name]


def ping() -> bool:
    """Return True if MongoDB responds to ping. Used by health checks."""
    try:
        get_client().admin.command("ping")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError, PyMongoError):
        logger.warning("MongoDB ping failed", exc_info=True)
        return False


def close_client() -> None:
    """Close the process-wide client. Useful in tests."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
