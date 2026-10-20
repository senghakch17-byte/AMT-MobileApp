from datetime import datetime, timezone

import jwt

from app.main import app
from app.schemas.event import EventBase

API = "/events"


async def test_event_routes_require_authentication(client):
    assert (await client.get(API)).status_code == 401
    assert (await client.get(API, headers={"Authorization": "Bearer bad"})).status_code == 401
    assert (await client.post(API, json={}, headers={"Authorization": "Bearer bad"})).status_code == 401


async def test_event_route_validation_and_ids_are_enforced(client):
    headers = {"Authorization": "Bearer bad"}
    assert (await client.get(f"{API}/not-an-object-id", headers=headers)).status_code == 401


async def test_admin_can_create_event_with_mocked_persistence(client, monkeypatch):
    from app.api import events

    class FakeEvent:
        def __init__(self, **data):
            self.__dict__.update(data)
            self.id = "a" * 24
            self.images = []
            self.created_at = self.updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)

        async def insert(self):
            return None

    async def invalidate(*_):
        return None

    published = []

    async def publish(event):
        published.append(event)

    monkeypatch.setattr(events, "Event", FakeEvent)
    monkeypatch.setattr(events, "invalidate_event", invalidate)
    monkeypatch.setattr(events, "publish_notification", publish)
    token = jwt.encode({"id": "admin-1", "emailid": "admin@example.com", "role": "admin"}, "event-test-secret-0123456789abcdef", algorithm="HS256")
    payload = {"title": "Test event", "description": "Long enough event description", "location": "Hall", "start_at": "2026-01-02T00:00:00Z"}
    response = await client.post(API, json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    assert response.json()["created_by"] == "admin-1"
    assert published == []

    response = await client.post(
        API,
        json={**payload, "status": "published"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert published[0]["type"] == "event.published"
    assert published[0]["recipient_role"] == "user"


def test_event_schema_normalizes_timezone_and_rejects_inverted_dates():
    event = EventBase(title="Test event", description="Long enough event description", location="Hall", start_at=datetime(2026, 1, 1), end_at=datetime(2026, 1, 1, 1, tzinfo=timezone.utc))
    assert event.start_at.tzinfo == timezone.utc
    try:
        EventBase(title="Test event", description="Long enough event description", location="Hall", start_at="2026-01-02T00:00:00Z", end_at="2026-01-01T00:00:00Z")
    except ValueError as exc:
        assert "end_at must be on or after start_at" in str(exc)
    else:
        raise AssertionError("inverted event dates accepted")


def test_active_event_routes_are_registered():
    paths = app.openapi()["paths"]
    assert API in paths
    assert f"{API}/{{event_id}}" in paths
    assert f"{API}/{{event_id}}/images" not in paths