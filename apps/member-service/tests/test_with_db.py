"""End-to-end flows against a real MongoDB. Skipped automatically when none is reachable.

    MONGODB_TEST_URI=mongodb://localhost:27017 uv run pytest

Uses the throwaway database `member_service_test` (dropped afterwards).
"""
from datetime import date

from tests.conftest import make_token

API = "/api/v1/members"
PDF = b"%PDF-1.4\n%fake but correctly-signed pdf\n"


async def _upload(client, headers, title="Diploma", **form):
    return await client.post(
        f"{API}/me/documents",
        headers=headers,
        data={"title": title, **form},
        files={"file": ("diploma.pdf", PDF)},
    )


async def test_profile_created_on_first_access_and_editable(db_client, member_headers):
    r = await db_client.get(f"{API}/me", headers=member_headers)
    assert r.status_code == 200
    body = r.json()
    assert (body["user_id"], body["email"], body["role"]) == ("user-1", "user-1@example.com", "member")

    r = await db_client.patch(
        f"{API}/me",
        headers=member_headers,
        json={"full_name": "Yiyao Test", "phone": "+855 12 345 678", "date_of_birth": "1999-05-17"},
    )
    assert r.status_code == 200
    assert r.json()["date_of_birth"] == "1999-05-17"

    again = (await db_client.get(f"{API}/me", headers=member_headers)).json()
    assert again["id"] == body["id"]  # no duplicate profile
    assert again["full_name"] == "Yiyao Test"
    assert again["date_of_birth"] == "1999-05-17"  # survives the Mongo round trip


async def test_profile_follows_token_claims(db_client):
    await db_client.get(f"{API}/me", headers=make_token("user-9", email="old@example.com"))
    r = await db_client.get(f"{API}/me", headers=make_token("user-9", role="admin", email="new@example.com"))
    assert (r.json()["email"], r.json()["role"]) == ("new@example.com", "admin")


async def test_admin_lists_and_searches_users(db_client, member_headers, other_headers, admin_headers):
    await db_client.get(f"{API}/me", headers=member_headers)
    await db_client.get(f"{API}/me", headers=other_headers)
    await db_client.patch(f"{API}/me", headers=member_headers, json={"full_name": "Sokha Chan"})

    r = await db_client.get(API, headers=admin_headers)
    assert r.status_code == 200
    assert {m["user_id"] for m in r.json()} >= {"user-1", "user-2"}
    assert r.headers["X-Total-Count"] == str(len(r.json()))

    found = await db_client.get(API, params={"q": "sokha"}, headers=admin_headers)
    assert [m["user_id"] for m in found.json()] == ["user-1"]

    literal = await db_client.get(API, params={"q": ".*"}, headers=admin_headers)  # not a regex
    assert literal.json() == []

    page = await db_client.get(API, params={"limit": 1, "skip": 0}, headers=admin_headers)
    assert len(page.json()) == 1 and int(page.headers["X-Total-Count"]) >= 2


async def test_view_profile_admin_and_self_only(db_client, member_headers, other_headers, admin_headers):
    await db_client.get(f"{API}/me", headers=member_headers)
    assert (await db_client.get(f"{API}/user-1", headers=admin_headers)).status_code == 200
    assert (await db_client.get(f"{API}/user-1", headers=member_headers)).status_code == 200
    assert (await db_client.get(f"{API}/user-1", headers=other_headers)).status_code == 403
    assert (await db_client.get(f"{API}/nobody", headers=admin_headers)).status_code == 404


async def test_document_upload_history_and_download(db_client, member_headers, other_headers, admin_headers):
    r = await _upload(db_client, member_headers, doc_type="certificate", document_date="2020-06-30")
    assert r.status_code == 201
    doc = r.json()
    assert doc["doc_type"] == "certificate" and doc["document_date"] == "2020-06-30"
    assert doc["content_type"] == "application/pdf" and doc["size_bytes"] == len(PDF)
    assert "stored_filename" not in doc
    await _upload(db_client, member_headers, title="Receipt", doc_type="receipt")

    mine = await db_client.get(f"{API}/me/documents", headers=member_headers)
    assert [d["title"] for d in mine.json()] == ["Receipt", "Diploma"]  # newest first
    assert mine.headers["X-Total-Count"] == "2"

    filtered = await db_client.get(f"{API}/me/documents", params={"doc_type": "certificate"}, headers=member_headers)
    assert [d["title"] for d in filtered.json()] == ["Diploma"]

    as_admin = await db_client.get(f"{API}/user-1/documents", headers=admin_headers)
    assert len(as_admin.json()) == 2

    dl = await db_client.get(f"{API}/me/documents/{doc['id']}/download", headers=member_headers)
    assert dl.status_code == 200 and dl.content == PDF
    assert "diploma.pdf" in dl.headers["content-disposition"]
    assert (await db_client.get(f"{API}/user-1/documents/{doc['id']}/download", headers=admin_headers)).content == PDF

    # another member can neither list nor fetch it, even through their own /me route
    assert (await db_client.get(f"{API}/user-1/documents", headers=other_headers)).status_code == 403
    assert (await db_client.get(f"{API}/me/documents", headers=other_headers)).json() == []
    assert (await db_client.get(f"{API}/me/documents/{doc['id']}/download", headers=other_headers)).status_code == 404


async def test_document_date_today_is_accepted(db_client, member_headers):
    r = await _upload(db_client, member_headers, document_date=date.today().isoformat())
    assert r.status_code == 201
