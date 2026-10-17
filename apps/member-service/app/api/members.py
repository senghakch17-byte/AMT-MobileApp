import re

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from beanie.operators import Or, RegEx
from pymongo.errors import DuplicateKeyError

from app.api.deps import get_current_user, require_admin, require_self_or_admin
from app.core.security import CurrentUser
from app.database.models import Member
from app.schemas.member import MemberResponse, MemberUpdate
from app.utils.helpers import utcnow

router = APIRouter(prefix="/members", tags=["Members"])


async def _get_or_create_member(user: CurrentUser) -> Member:
    """Profiles are created lazily from the JWT claims the first time a user shows up."""
    member = await Member.find_one(Member.user_id == user.id)
    if member is None:
        member = Member(user_id=user.id, email=user.emailid, role=user.role)
        try:
            await member.insert()
        except DuplicateKeyError:  # two first requests raced; the other one won
            member = await Member.find_one(Member.user_id == user.id)
            if member is None:
                raise
        return member
    if member.email != user.emailid or member.role != user.role:  # keep in sync with auth
        member.email, member.role = user.emailid, user.role
        member.updated_at = utcnow()
        await member.save()
    return member


async def _get_or_404(user_id: str) -> Member:
    member = await Member.find_one(Member.user_id == user_id)
    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    return member


# ---------- Any logged-in user: own profile ----------
# NOTE: "/me" routes are declared before "/{user_id}" so "me" is never read as an id.

@router.get("/me", response_model=MemberResponse)
async def get_my_profile(user: CurrentUser = Depends(get_current_user)):
    return await _get_or_create_member(user)


@router.patch("/me", response_model=MemberResponse)
async def update_my_profile(
    payload: MemberUpdate, user: CurrentUser = Depends(get_current_user)
):
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields to update")
    member = await _get_or_create_member(user)
    for field, value in changes.items():
        setattr(member, field, value)
    member.updated_at = utcnow()
    await member.save()
    return member


# ---------- Admin: view all users ----------

@router.get("", response_model=list[MemberResponse])
async def list_members(
    response: Response,
    q: str | None = Query(None, min_length=1, max_length=100, description="Search name or email"),
    role: str | None = Query(None, description="Filter by role, e.g. admin or member"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _: CurrentUser = Depends(require_admin),
):
    conditions = []
    if q:
        pattern = re.escape(q)  # user input is matched literally, never as a regex
        conditions.append(
            Or(RegEx(Member.full_name, pattern, "i"), RegEx(Member.email, pattern, "i"))
        )
    if role:
        conditions.append(Member.role == role)
    query = Member.find(*conditions)
    response.headers["X-Total-Count"] = str(await query.count())
    return await query.sort("-created_at").skip(skip).limit(limit).to_list()


# ---------- Admin (any member) or the member themselves: view profile ----------

@router.get("/{user_id}", response_model=MemberResponse)
async def get_member_profile(
    user_id: str, _: CurrentUser = Depends(require_self_or_admin)
):
    return await _get_or_404(user_id)
