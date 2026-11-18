"""Checks decided before any database call: auth, roles, validation, schema rules, routing."""
from datetime import datetime, timedelta, timezone

import pytest

from app.main import app
from app.schemas.booking import BookingCreate
from app.schemas.room import RoomBase

API = ""
ROOM_ID = "a" * 24


def _slot(hours_from_now: float = 24, length_minutes: int = 60) -> dict:
    start = datetime.now(timezone.utc) + timedelta(hours=hours_from_now)
    return {
        "room_id": ROOM_ID,
        "start_at": start.isoformat(),
        "end_at": (start + timedelta(minutes=length_minutes)).isoformat(),
        "purpose": "Group study",
    }


# ---------- authentication ----------

async def test_missing_token_rejected(client):
    for path in ("/rooms", "/me"):
        assert (await client.get(f"{API}{path}")).status_code in (401, 403)


async def test_bad_token_rejected(client):
    r = await client.get(f"{API}/rooms", headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401


# ---------- admin-only endpoints reject members ----------

@pytest.mark.parametrize(
    "method,path,body",
    [
        ("POST", "/rooms", {"name": "Quiet Room", "location": "Floor 2", "capacity": 4}),
        ("PATCH", f"/rooms/{ROOM_ID}", {"capacity": 6}),
        ("DELETE", f"/rooms/{ROOM_ID}", None),
        ("GET", "/", None),
        ("POST", f"/{ROOM_ID}/approve", None),
        ("POST", f"/{ROOM_ID}/reject", None),
    ],
)
async def test_member_cannot_use_admin_endpoints(client, member_headers, method, path, body):
    r = await client.request(method, f"{API}{path}", headers=member_headers, json=body)
    assert r.status_code == 403


# ---------- room validation ----------

@pytest.mark.parametrize(
    "body",
    [
        {"name": "A", "location": "Floor 2", "capacity": 4},        # name too short
        {"name": "Quiet Room", "location": "Floor 2", "capacity": 0},  # capacity < 1
        {"name": "Quiet Room", "capacity": 4},                        # location missing
    ],
)
async def test_invalid_room_rejected(client, admin_headers, body):
    assert (await client.post(f"{API}/rooms", json=body, headers=admin_headers)).status_code == 422


async def test_empty_room_update_rejected(client, admin_headers):
    r = await client.patch(f"{API}/rooms/{ROOM_ID}", json={}, headers=admin_headers)
    assert r.status_code == 400


def test_room_schema_cleans_input():
    room = RoomBase(
        name="  Study Room 1 ", location=" Floor 2", capacity=6,
        amenities=["Whiteboard", " Projector ", "Whiteboard", ""],
    )
    assert room.name == "Study Room 1" and room.location == "Floor 2"
    assert room.amenities == ["Whiteboard", "Projector"]  # trimmed, de-duplicated, blanks dropped
    assert room.is_active is True


# ---------- availability window validation ----------

async def test_availability_requires_valid_window(client, member_headers):
    now = datetime.now(timezone.utc)
    url = f"{API}/rooms/{ROOM_ID}/availability"
    backwards = {"start": now.isoformat(), "end": (now - timedelta(hours=1)).isoformat()}
    assert (await client.get(url, params=backwards, headers=member_headers)).status_code == 422
    too_long = {"start": now.isoformat(), "end": (now + timedelta(days=32)).isoformat()}
    assert (await client.get(url, params=too_long, headers=member_headers)).status_code == 422
    assert (await client.get(url, headers=member_headers)).status_code == 422  # window is required


# ---------- booking validation (rules that need no database) ----------

async def test_booking_in_the_past_rejected(client, member_headers):
    r = await client.post(f"{API}/", json=_slot(hours_from_now=-3), headers=member_headers)
    assert r.status_code == 422 and "future" in r.json()["detail"]


async def test_booking_too_short_rejected(client, member_headers):
    r = await client.post(f"{API}/", json=_slot(length_minutes=10), headers=member_headers)
    assert r.status_code == 422 and "at least" in r.json()["detail"]


async def test_booking_too_long_rejected(client, member_headers):
    r = await client.post(f"{API}/", json=_slot(length_minutes=5 * 60), headers=member_headers)
    assert r.status_code == 422 and "at most" in r.json()["detail"]


async def test_booking_end_before_start_rejected(client, member_headers):
    body = _slot()
    body["start_at"], body["end_at"] = body["end_at"], body["start_at"]
    assert (await client.post(f"{API}/", json=body, headers=member_headers)).status_code == 422


async def test_booking_requires_purpose_and_room(client, member_headers):
    body = _slot()
    del body["purpose"]
    assert (await client.post(f"{API}/", json=body, headers=member_headers)).status_code == 422
    body = _slot()
    body["room_id"] = "not-an-id"
    assert (await client.post(f"{API}/", json=body, headers=member_headers)).status_code == 422


def test_naive_booking_times_are_treated_as_utc():
    b = BookingCreate(
        room_id=ROOM_ID, start_at="2030-01-01T09:00:00", end_at="2030-01-01T10:00:00", purpose="Study"
    )
    assert b.start_at.tzinfo is not None and b.start_at.utcoffset() == timedelta(0)


def test_booking_times_with_offset_are_converted_to_utc():
    b = BookingCreate(
        room_id=ROOM_ID, start_at="2030-01-01T09:00:00+07:00", end_at="2030-01-01T10:00:00+07:00",
        purpose="Study",
    )
    assert b.start_at == datetime(2030, 1, 1, 2, 0, tzinfo=timezone.utc)


# ---------- routing ----------

def test_me_route_registered_before_booking_id_route():
    # "/me" must win over "/{booking_id}", otherwise "me" would be read as a booking id.
    paths = list(app.openapi()["paths"])
    assert paths.index(f"{API}/me") < paths.index(f"{API}/{{booking_id}}")
