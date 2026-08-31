import pytest
from django.conf import settings


@pytest.fixture
def owner_session(client):
    """Pretend an Owner/Admin is logged in without hitting MongoDB."""
    session = client.session
    session["tourops_user"] = {
        "id": "000000000000000000000001",
        "email": "owner@tourops.local",
        "first_name": "Owner",
        "last_name": "Admin",
        "role": "OWNER_ADMIN",
    }
    session.save()
    # Signed-cookie sessions store data in the cookie value (session_key).
    client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
    return client
