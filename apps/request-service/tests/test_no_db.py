from datetime import date

import jwt

from app.main import app
from app.schemas.leave_request import LeaveRequestBase
from app.schemas.pre_scholarship import PreScholarshipBase

API = ""


async def test_health_and_authentication_boundary(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert (await client.get("/leave-requests")).status_code == 401
    assert (await client.get("/leave-requests", headers={"Authorization": "Bearer bad"})).status_code == 401


async def test_active_post_routes_reject_invalid_tokens_before_database(client):
    headers = {"Authorization": "Bearer bad"}
    assert (await client.post("/leave-requests", json={}, headers=headers)).status_code == 401
    assert (await client.post("/pre-scholarship-registrations", json={}, headers=headers)).status_code == 401


async def test_authenticated_user_can_create_leave_request_with_mocked_persistence(client, monkeypatch):
    from datetime import datetime, timezone
    from app.api import leave_requests

    class FakeLeaveRequest:
        @classmethod
        async def find_one(cls, *_):
            return None

        def __init__(self, **data):
            self.__dict__.update(data)
            self.id = "a" * 24
            self.status = "pending"
            self.reviewed_by = self.review_comment = self.reviewed_at = self.cancelled_at = None
            self.created_at = self.updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)

        async def insert(self):
            return None

    async def bump(*_):
        return None

    async def no_overlap(*_):
        return None

    monkeypatch.setattr(leave_requests, "LeaveRequest", FakeLeaveRequest)
    monkeypatch.setattr(leave_requests, "bump_version", bump)
    monkeypatch.setattr(leave_requests, "_ensure_no_overlap", no_overlap)
    token = jwt.encode({"id": "user-1", "emailid": "user@example.com", "role": "user"}, "request-test-secret-0123456789abcdef", algorithm="HS256")
    response = await client.post("/leave-requests", json={"leave_type": "sick", "start_date": "2026-02-01", "end_date": "2026-02-02", "reason": "Long enough reason"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    assert response.json()["student_id"] == "user-1"


def test_leave_schema_rejects_bad_ranges_and_short_reason():
    try:
        LeaveRequestBase(leave_type="sick", start_date=date(2026, 2, 2), end_date=date(2026, 2, 1), reason="long enough reason")
    except ValueError as exc:
        assert "end_date must be on or after start_date" in str(exc)
    else:
        raise AssertionError("invalid date range accepted")
    try:
        LeaveRequestBase(leave_type="sick", start_date=date(2026, 2, 1), end_date=date(2026, 2, 1), reason="short")
    except ValueError:
        pass
    else:
        raise AssertionError("short reason accepted")


def test_pre_scholarship_schema_enforces_type_requirements():
    base = dict(academic_year="2026-2027", full_name="User Name", date_of_birth="2000-01-01", gender="other", phone="12345678", address="Test address", school_name="Test School", grade_level="12", guardian_name="Guardian Name", guardian_phone="12345678", guardian_relationship="parent", statement="This statement has enough content.")
    for scholarship_type, field in [("need_based", "monthly_family_income"), ("merit", "academic_average")]:
        try:
            PreScholarshipBase(scholarship_type=scholarship_type, **base)
        except ValueError as exc:
            assert field in str(exc)
        else:
            raise AssertionError(f"{scholarship_type} requirement accepted")


def test_only_documented_routes_are_registered():
    paths = app.openapi()["paths"]
    assert "/leave-requests" in paths
    assert "/pre-scholarship-registrations" in paths
    assert "/pre-scholarship-registrations/{request_id}" not in paths