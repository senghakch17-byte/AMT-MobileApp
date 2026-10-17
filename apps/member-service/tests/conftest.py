import os
import tempfile
from datetime import datetime, timedelta, timezone

# Settings are read at import time, so configure the environment first.
# The test database name is forced so tests can never touch real data.
os.environ["JWT_SECRET"] = "member-service-test-secret-0123456789"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["MONGODB_URI"] = os.environ.get("MONGODB_TEST_URI", "mongodb://localhost:27017")
os.environ["MONGODB_DB_NAME"] = "member_service_test"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="member-service-uploads-")
os.environ["PUBLIC_BASE_URL"] = "http://testserver"

import httpx  # noqa: E402
import jwt  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402

from app.main import app  # noqa: E402


def make_token(user_id: str, role: str = "member", email: str | None = None) -> dict:
    payload = {
        "id": user_id,
        "emailid": email or f"{user_id}@example.com",
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def member_headers() -> dict:
    return make_token("user-1")


@pytest.fixture
def other_headers() -> dict:
    return make_token("user-2")


@pytest.fixture
def admin_headers() -> dict:
    return make_token("admin-1", role="admin")


@pytest_asyncio.fixture
async def client():
    """App without startup: enough for everything that is decided before the database."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest_asyncio.fixture
async def db_client():
    """Full app with a real MongoDB. Skips when none is reachable."""
    from app.database import mongodb

    try:
        async with app.router.lifespan_context(app):
            db = mongodb.client[os.environ["MONGODB_DB_NAME"]]
            await db["members"].delete_many({})
            await db["member_documents"].delete_many({})
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
                yield c
            await mongodb.client.drop_database(os.environ["MONGODB_DB_NAME"])
    except Exception as exc:  # noqa: BLE001
        if "ServerSelectionTimeout" in type(exc).__name__ or "ConnectionFailure" in type(exc).__name__:
            pytest.skip(f"MongoDB not reachable ({type(exc).__name__}); set MONGODB_TEST_URI")
        raise
