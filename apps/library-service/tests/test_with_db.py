"""End-to-end flows against a real MongoDB. Skipped automatically when none is reachable.

    MONGODB_TEST_URI=mongodb://localhost:27017 uv run pytest

Uses the throwaway database `library_service_test` (dropped afterwards).
"""
from datetime import datetime, timedelta, timezone

from app.core.config import settings

API = "/api/v1"


def slot(day: int = 1, hour: int = 9, hours: int = 1) -> dict:
    """A future [start, end) window: `day` days from today at `hour`:00 UTC."""
    start = datetime.now(timezone.utc).replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=day)
    return {"start_at": start.isoformat(), "end_at": (start + timedelta(hours=hours)).isoformat()}


async def make_room(client, admin_headers, name="Study Room 1", capacity=6, **extra):
    r = await client.post(
        f"{API}/rooms",
        headers=admin_headers,
        json={"name": name, "location": "Floor 2", "capacity": capacity, **extra},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def book(client, headers, room, purpose="Group study", attendees=2, **when):
    return await client.post(
        f"{API}/bookings",
        headers=headers,
        json={"room_id": room["id"], "purpose": purpose, "attendees": attendees, **(when or slot())},
    )


# ---------- rooms ----------

async def test_room_crud_and_visibility(db_client, admin_headers, member_headers):
    room = await make_room(db_client, admin_headers, amenities=["Whiteboard"])
    assert (await make_room_dup(db_client, admin_headers)).status_code == 409

    r = await db_client.patch(f"{API}/rooms/{room['id']}", headers=admin_headers, json={"capacity": 8})
    assert r.status_code == 200 and r.json()["capacity"] == 8

    assert (await db_client.get(f"{API}/rooms/{room['id']}", headers=member_headers)).status_code == 200

    await db_client.patch(f"{API}/rooms/{room['id']}", headers=admin_headers, json={"is_active": False})
    assert (await db_client.get(f"{API}/rooms/{room['id']}", headers=member_headers)).status_code == 404
    assert (await db_client.get(f"{API}/rooms/{room['id']}", headers=admin_headers)).status_code == 200
    assert (await db_client.get(f"{API}/rooms", headers=member_headers)).json() == []
    assert len((await db_client.get(f"{API}/rooms", headers=admin_headers)).json()) == 1

    assert (await db_client.delete(f"{API}/rooms/{room['id']}", headers=admin_headers)).status_code == 204
    assert (await db_client.get(f"{API}/rooms/{room['id']}", headers=admin_headers)).status_code == 404


async def make_room_dup(client, admin_headers):
    return await client.post(
        f"{API}/rooms", headers=admin_headers, json={"name": "Study Room 1", "location": "Floor 3", "capacity": 2}
    )


async def test_room_search_and_filters(db_client, admin_headers, member_headers):
    await make_room(db_client, admin_headers, name="Quiet Room", capacity=2, amenities=["Power outlets"])
    await make_room(db_client, admin_headers, name="Seminar Hall", capacity=30, amenities=["Projector"])

    r = await db_client.get(f"{API}/rooms", headers=member_headers)
    assert [x["name"] for x in r.json()] == ["Quiet Room", "Seminar Hall"]
    assert r.headers["X-Total-Count"] == "2"

    big = await db_client.get(f"{API}/rooms", params={"min_capacity": 10}, headers=member_headers)
    assert [x["name"] for x in big.json()] == ["Seminar Hall"]
    proj = await db_client.get(f"{API}/rooms", params={"amenity": "projector"}, headers=member_headers)
    assert [x["name"] for x in proj.json()] == ["Seminar Hall"]
    assert (await db_client.get(f"{API}/rooms", params={"q": "quiet"}, headers=member_headers)).json()[0]["name"] == "Quiet Room"
    assert (await db_client.get(f"{API}/rooms", params={"q": ".*"}, headers=member_headers)).json() == []  # literal


async def test_room_with_booking_history_cannot_be_deleted(db_client, admin_headers, member_headers):
    room = await make_room(db_client, admin_headers)
    await book(db_client, member_headers, room)
    assert (await db_client.delete(f"{API}/rooms/{room['id']}", headers=admin_headers)).status_code == 409


# ---------- booking with approval ----------

async def test_booking_approval_flow(db_client, admin_headers, member_headers, other_headers):
    room = await make_room(db_client, admin_headers)
    first = await book(db_client, member_headers, room)
    assert first.status_code == 201
    first = first.json()
    assert first["status"] == "pending" and first["room_name"] == "Study Room 1"
    assert first["user_id"] == "user-1"

    # pending bookings don't hold the room, so a second user can also ask for it
    second = (await book(db_client, other_headers, room)).json()
    assert second["status"] == "pending"

    window = {"start": slot(0)["start_at"], "end": slot(3)["end_at"]}
    busy = await db_client.get(f"{API}/rooms/{room['id']}/availability", params=window, headers=other_headers)
    assert busy.json() == []

    approved = await db_client.post(
        f"{API}/bookings/{first['id']}/approve", headers=admin_headers, json={"note": "Enjoy"}
    )
    assert approved.status_code == 200
    body = approved.json()
    assert body["status"] == "approved" and body["decided_by"] == "admin-1" and body["admin_note"] == "Enjoy"

    busy = await db_client.get(f"{API}/rooms/{room['id']}/availability", params=window, headers=other_headers)
    assert len(busy.json()) == 1 and set(busy.json()[0]) == {"start_at", "end_at"}  # no user details

    # the slot is now taken: the other request can't be approved, only rejected
    assert (await db_client.post(f"{API}/bookings/{second['id']}/approve", headers=admin_headers)).status_code == 409
    rejected = await db_client.post(
        f"{API}/bookings/{second['id']}/reject", headers=admin_headers, json={"note": "Slot taken"}
    )
    assert rejected.json()["status"] == "rejected" and rejected.json()["admin_note"] == "Slot taken"

    # decisions are final
    assert (await db_client.post(f"{API}/bookings/{first['id']}/approve", headers=admin_headers)).status_code == 409
    assert (await db_client.post(f"{API}/bookings/{second['id']}/reject", headers=admin_headers)).status_code == 409

    # new requests for a taken slot are refused up front
    assert (await book(db_client, other_headers, room, **slot())).status_code == 409


async def test_booking_rules_against_room(db_client, admin_headers, member_headers):
    room = await make_room(db_client, admin_headers, capacity=4)
    assert (await book(db_client, member_headers, room, attendees=5)).status_code == 422
    assert (await book(db_client, member_headers, {"id": "b" * 24})).status_code == 404

    assert (await book(db_client, member_headers, room, **slot(hour=9))).status_code == 201
    # one person can't hold two overlapping requests, even in different rooms
    other_room = await make_room(db_client, admin_headers, name="Study Room 2")
    assert (await book(db_client, member_headers, other_room, **slot(hour=9))).status_code == 409
    assert (await book(db_client, member_headers, other_room, **slot(hour=10))).status_code == 201  # adjacent is fine

    await db_client.patch(f"{API}/rooms/{room['id']}", headers=admin_headers, json={"is_active": False})
    assert (await book(db_client, member_headers, room, **slot(day=2))).status_code == 404


# ---------- cancel ----------

async def test_cancel_rules(db_client, admin_headers, member_headers, other_headers):
    room = await make_room(db_client, admin_headers)
    b = (await book(db_client, member_headers, room)).json()

    assert (await db_client.post(f"{API}/bookings/{b['id']}/cancel", headers=other_headers)).status_code == 404
    done = await db_client.post(f"{API}/bookings/{b['id']}/cancel", headers=member_headers)
    assert done.status_code == 200 and done.json()["status"] == "cancelled"
    assert (await db_client.post(f"{API}/bookings/{b['id']}/cancel", headers=member_headers)).status_code == 409

    # an admin can cancel an approved booking, which frees the slot again
    again = (await book(db_client, member_headers, room)).json()
    await db_client.post(f"{API}/bookings/{again['id']}/approve", headers=admin_headers)
    cancelled = await db_client.post(f"{API}/bookings/{again['id']}/cancel", headers=admin_headers)
    assert cancelled.json()["status"] == "cancelled" and cancelled.json()["decided_by"] == "admin-1"
    assert (await book(db_client, other_headers, room)).status_code == 201


# ---------- viewing & history ----------

async def test_booking_visibility_and_admin_history(db_client, admin_headers, member_headers, other_headers):
    room = await make_room(db_client, admin_headers)
    mine = (await book(db_client, member_headers, room, **slot(day=1))).json()
    theirs = (await book(db_client, other_headers, room, **slot(day=2))).json()
    await db_client.post(f"{API}/bookings/{theirs['id']}/approve", headers=admin_headers)

    # members see only their own bookings
    me = await db_client.get(f"{API}/bookings/me", headers=member_headers)
    assert [b["id"] for b in me.json()] == [mine["id"]] and me.headers["X-Total-Count"] == "1"
    assert (await db_client.get(f"{API}/bookings/{mine['id']}", headers=member_headers)).status_code == 200
    assert (await db_client.get(f"{API}/bookings/{mine['id']}", headers=other_headers)).status_code == 404
    assert (await db_client.get(f"{API}/bookings/{mine['id']}", headers=admin_headers)).status_code == 200

    # admin history: everything, newest slot first, with filters
    everything = await db_client.get(f"{API}/bookings", headers=admin_headers)
    assert [b["id"] for b in everything.json()] == [theirs["id"], mine["id"]]
    assert everything.headers["X-Total-Count"] == "2"
    pending = await db_client.get(f"{API}/bookings", params={"status": "pending"}, headers=admin_headers)
    assert [b["id"] for b in pending.json()] == [mine["id"]]
    by_user = await db_client.get(f"{API}/bookings", params={"user_id": "user-2"}, headers=admin_headers)
    assert [b["id"] for b in by_user.json()] == [theirs["id"]]
    by_room = await db_client.get(f"{API}/bookings", params={"room_id": room["id"]}, headers=admin_headers)
    assert len(by_room.json()) == 2
    ranged = await db_client.get(
        f"{API}/bookings", params={"start_from": slot(day=2, hour=0)["start_at"]}, headers=admin_headers
    )
    assert [b["id"] for b in ranged.json()] == [theirs["id"]]


# ---------- approval switched off ----------

async def test_auto_approval_when_approval_not_required(db_client, admin_headers, member_headers, other_headers, monkeypatch):
    monkeypatch.setattr(settings, "REQUIRE_BOOKING_APPROVAL", False)
    room = await make_room(db_client, admin_headers)

    r = await book(db_client, member_headers, room)
    assert r.status_code == 201
    assert r.json()["status"] == "approved" and r.json()["decided_by"] == "system"

    assert (await book(db_client, other_headers, room)).status_code == 409
    history = await db_client.get(f"{API}/bookings", headers=admin_headers)
    assert history.headers["X-Total-Count"] == "1"  # the refused request left no trace


# ---------- books ----------

async def test_book_catalog(db_client, admin_headers, member_headers):
    dune = await db_client.post(
        f"{API}/books", headers=admin_headers,
        json={"title": "Dune", "author": "Frank Herbert", "isbn": "978-0-441-17271-9", "category": "Sci-Fi", "copies": 3},
    )
    assert dune.status_code == 201
    dune = dune.json()
    assert dune["isbn"] == "9780441172719" and dune["category"] == "sci-fi"

    dup = await db_client.post(
        f"{API}/books", headers=admin_headers,
        json={"title": "Dune (2nd copy)", "author": "Frank Herbert", "isbn": "9780441172719"},
    )
    assert dup.status_code == 409

    # books without an ISBN don't collide with each other
    for title in ("Local Folk Tales", "Khmer Cooking"):
        r = await db_client.post(
            f"{API}/books", headers=admin_headers, json={"title": title, "author": "Various", "category": "culture"}
        )
        assert r.status_code == 201

    listing = await db_client.get(f"{API}/books", headers=member_headers)
    assert [b["title"] for b in listing.json()] == ["Dune", "Khmer Cooking", "Local Folk Tales"]
    assert listing.headers["X-Total-Count"] == "3"
    assert [b["title"] for b in (await db_client.get(f"{API}/books", params={"q": "herbert"}, headers=member_headers)).json()] == ["Dune"]
    cats = await db_client.get(f"{API}/books", params={"category": "Culture"}, headers=member_headers)
    assert len(cats.json()) == 2

    patched = await db_client.patch(f"{API}/books/{dune['id']}", headers=admin_headers, json={"copies": 5})
    assert patched.json()["copies"] == 5
    assert (await db_client.get(f"{API}/books/{dune['id']}", headers=member_headers)).json()["copies"] == 5

    assert (await db_client.delete(f"{API}/books/{dune['id']}", headers=admin_headers)).status_code == 204
    assert (await db_client.get(f"{API}/books/{dune['id']}", headers=member_headers)).status_code == 404
