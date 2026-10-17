"""Checks that are decided before any database call: auth, roles, validation, uploads."""
from datetime import date, datetime, time, timedelta, timezone

import pytest
from beanie.odm.utils.encoder import Encoder

from app.main import app
from app.schemas.member import MemberBase, MemberResponse
from app.utils.storage import _sniff_type

API = "/api/v1/members"
PDF = b"%PDF-1.4\n%fake but correctly-signed pdf\n"


# ---------- authentication ----------

async def test_missing_token_rejected(client):
    r = await client.get(f"{API}/me")
    assert r.status_code in (401, 403)


async def test_bad_token_rejected(client):
    r = await client.get(f"{API}/me", headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401


# ---------- authorization ----------

async def test_member_cannot_list_all_users(client, member_headers):
    assert (await client.get(API, headers=member_headers)).status_code == 403


async def test_member_cannot_view_other_profile(client, member_headers):
    assert (await client.get(f"{API}/user-2", headers=member_headers)).status_code == 403


async def test_member_cannot_view_other_document_history(client, member_headers):
    assert (await client.get(f"{API}/user-2/documents", headers=member_headers)).status_code == 403


async def test_member_cannot_download_other_document(client, member_headers):
    r = await client.get(f"{API}/user-2/documents/{'a' * 24}/download", headers=member_headers)
    assert r.status_code == 403


# ---------- profile validation ----------

async def test_empty_profile_update_rejected(client, member_headers):
    assert (await client.patch(f"{API}/me", json={}, headers=member_headers)).status_code == 400


@pytest.mark.parametrize(
    "body",
    [
        {"phone": "abc"},
        {"full_name": "x"},
        {"date_of_birth": (date.today() + timedelta(days=1)).isoformat()},
    ],
)
async def test_invalid_profile_fields_rejected(client, member_headers, body):
    assert (await client.patch(f"{API}/me", json=body, headers=member_headers)).status_code == 422


# ---------- upload validation ----------

async def _upload(client, headers, content=PDF, filename="a.pdf", **form):
    data = {"title": "Diploma", **form}
    return await client.post(
        f"{API}/me/documents", headers=headers, data=data, files={"file": (filename, content)}
    )


async def test_upload_requires_title(client, member_headers):
    r = await client.post(
        f"{API}/me/documents", headers=member_headers, files={"file": ("a.pdf", PDF)}
    )
    assert r.status_code == 422


async def test_upload_rejects_wrong_file_type(client, member_headers):
    r = await _upload(client, member_headers, content=b"MZ\x90\x00 not a document", filename="evil.pdf")
    assert r.status_code == 415  # extension says pdf, content says otherwise


async def test_upload_rejects_empty_file(client, member_headers):
    assert (await _upload(client, member_headers, content=b"")).status_code == 400


async def test_upload_rejects_oversized_file(client, member_headers):
    big = PDF + b"0" * (10 * 1024 * 1024)
    assert (await _upload(client, member_headers, content=big)).status_code == 413


async def test_upload_rejects_future_document_date(client, member_headers):
    future = (date.today() + timedelta(days=2)).isoformat()
    assert (await _upload(client, member_headers, document_date=future)).status_code == 422


def test_sniff_detects_real_types():
    assert _sniff_type(PDF) == (".pdf", "application/pdf")
    assert _sniff_type(b"\xff\xd8\xff\xe0rest")[0] == ".jpg"
    assert _sniff_type(b"\x89PNG\r\n\x1a\nrest")[0] == ".png"
    assert _sniff_type(b"RIFF\x00\x00\x00\x00WEBPrest")[0] == ".webp"
    assert _sniff_type(b"<html>") is None


# ---------- routing ----------

def test_me_routes_registered_before_user_id_routes():
    # "/me" must win over "/{user_id}", otherwise "me" would be read as a user id.
    paths = list(app.openapi()["paths"])
    assert paths.index(f"{API}/me") < paths.index(f"{API}/{{user_id}}")
    assert paths.index(f"{API}/me/documents") < paths.index(f"{API}/{{user_id}}/documents")
    assert paths.index(f"{API}/me/documents/{{document_id}}/download") < paths.index(
        f"{API}/{{user_id}}/documents/{{document_id}}/download"
    )


# ---------- date round-trip through MongoDB's datetime-only storage ----------

def test_date_of_birth_survives_mongo_round_trip():
    encoded = Encoder().encode(MemberBase(date_of_birth=date(1999, 5, 17)))
    assert isinstance(encoded["date_of_birth"], datetime)  # what Mongo stores: midnight datetime
    assert encoded["date_of_birth"].time() == time.min
    stored = {**encoded, "date_of_birth": encoded["date_of_birth"].replace(tzinfo=timezone.utc)}  # tz_aware read
    now = datetime.now(timezone.utc)
    resp = MemberResponse.model_validate(
        {**stored, "id": "a" * 24, "user_id": "u", "email": "u@example.com", "role": "member",
         "created_at": now, "updated_at": now}
    )
    assert resp.date_of_birth == date(1999, 5, 17)
