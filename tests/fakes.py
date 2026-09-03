from __future__ import annotations

import copy
from bson import ObjectId


class FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeUpdateResult:
    def __init__(self, matched_count, modified_count):
        self.matched_count = matched_count
        self.modified_count = modified_count


class FakeCursor:
    def __init__(self, docs):
        self._docs = docs

    def limit(self, count):
        return FakeCursor(self._docs[:count])

    def sort(self, key, direction=1):
        reverse = direction == -1
        return FakeCursor(
            sorted(self._docs, key=lambda doc: (doc.get(key) is None, doc.get(key)), reverse=reverse)
        )

    def __iter__(self):
        return iter(self._docs)


class FakeCollection:
    def __init__(self):
        self.docs: list[dict] = []

    def _matches(self, document: dict, query: dict) -> bool:
        for key, expected in (query or {}).items():
            actual = document.get(key)
            if isinstance(expected, dict) and any(str(op).startswith("$") for op in expected):
                if "$ne" in expected and actual == expected["$ne"]:
                    return False
                if "$gte" in expected and (actual is None or actual < expected["$gte"]):
                    return False
                if "$lte" in expected and (actual is None or actual > expected["$lte"]):
                    return False
                if "$gt" in expected and (actual is None or actual <= expected["$gt"]):
                    return False
                if "$lt" in expected and (actual is None or actual >= expected["$lt"]):
                    return False
                continue
            if actual != expected:
                return False
        return True

    def find_one(self, query=None):
        for document in self.docs:
            if self._matches(document, query or {}):
                return copy.deepcopy(document)
        return None

    def find(self, query=None):
        return FakeCursor(
            [copy.deepcopy(document) for document in self.docs if self._matches(document, query or {})]
        )

    def insert_one(self, document):
        stored = copy.deepcopy(document)
        stored.setdefault("_id", ObjectId())
        self.docs.append(stored)
        return FakeInsertResult(stored["_id"])

    def update_one(self, query, update):
        for document in self.docs:
            if self._matches(document, query or {}):
                self._apply_update(document, update)
                return FakeUpdateResult(1, 1)
        return FakeUpdateResult(0, 0)

    def update_many(self, query, update):
        matched = modified = 0
        for document in self.docs:
            if self._matches(document, query or {}):
                matched += 1
                before = copy.deepcopy(document)
                self._apply_update(document, update)
                if document != before:
                    modified += 1
        return FakeUpdateResult(matched, modified)

    def find_one_and_update(self, query, update, upsert=False, return_document=None):
        target = None
        for document in self.docs:
            if self._matches(document, query or {}):
                target = document
                break
        if target is None:
            if not upsert:
                return None
            target = copy.deepcopy(query or {})
            target.setdefault("_id", ObjectId())
            self.docs.append(target)
        self._apply_update(target, update)
        return copy.deepcopy(target)

    def _apply_update(self, document: dict, update: dict) -> None:
        for key, amount in (update.get("$inc") or {}).items():
            document[key] = (document.get(key) or 0) + amount
        document.update(update.get("$set") or {})

    def count_documents(self, query=None):
        return sum(1 for document in self.docs if self._matches(document, query or {}))


class FakeMongo:
    def __init__(self):
        self._collections: dict[str, FakeCollection] = {}

    def get_collection(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection()
        return self._collections[name]
