import os
import tempfile

os.environ["JWT_SECRET"] = "event-test-secret-0123456789abcdef"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB_NAME"] = "event_service_test"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="event-service-uploads-")

import httpx  # noqa: E402
import pytest_asyncio  # noqa: E402

from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client