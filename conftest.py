import pytest
from django.conf import settings

from tests.fakes import FakeMongo


@pytest.fixture(autouse=True)
def fake_mongo(monkeypatch):
    mongo = FakeMongo()
    monkeypatch.setattr("core.database.get_collection", mongo.get_collection)
    monkeypatch.setattr("core.numbering.get_collection", mongo.get_collection)
    monkeypatch.setattr("apps.accounts.repositories.get_collection", mongo.get_collection)
    monkeypatch.setattr("apps.expenses.repositories.get_collection", mongo.get_collection)
    monkeypatch.setattr("apps.supplier_payments.repositories.get_collection", mongo.get_collection)
    monkeypatch.setattr("apps.reports.repositories.get_collection", mongo.get_collection)
    monkeypatch.setattr("apps.suppliers.repositories.get_collection", mongo.get_collection)
    monkeypatch.setattr("apps.packages.repositories.get_collection", mongo.get_collection)
    monkeypatch.setattr("apps.tours.repositories.get_collection", mongo.get_collection)
    return mongo


def _session_client(client, **user):
    session = client.session
    session["tourops_user"] = {
        "id": user.get("id", "000000000000000000000001"),
        "email": user.get("email", "owner@tourops.local"),
        "first_name": user.get("first_name", "Owner"),
        "last_name": user.get("last_name", "Admin"),
        "role": user.get("role", "OWNER_ADMIN"),
    }
    session.save()
    client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
    return client


@pytest.fixture
def owner_session(client):
    return _session_client(client)


@pytest.fixture
def agent_session(client):
    return _session_client(
        client,
        id="000000000000000000000002",
        email="agent@tourops.local",
        first_name="Amina",
        last_name="Agent",
        role="TRAVEL_AGENT",
    )


@pytest.fixture
def accountant_session(client):
    return _session_client(
        client,
        id="000000000000000000000003",
        email="accountant@tourops.local",
        first_name="Karim",
        last_name="Books",
        role="ACCOUNTANT",
    )
