import os

os.environ["JWT_SECRET"] = "request-test-secret-0123456789abcdef"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB_NAME"] = "request_service_test"

import httpx  # noqa: E402
import pytest_asyncio  # noqa: E402

from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client