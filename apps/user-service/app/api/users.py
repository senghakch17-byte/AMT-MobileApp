import re

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from beanie.operators import Or, RegEx
from pymongo.errors import DuplicateKeyError

from app.api.deps import get_current_user, require_admin, require_self_or_admin
from app.core.security import CurrentUser
from app.database.models import UserProfile
from app.schemas.user import AdminUserCreate, AdminUserUpdate, UserProfileResponse, UserProfileUpdate
from app.services.accounts import account_request
from app.utils.helpers import utcnow

router = APIRouter(tags=["Users"])


async def _get_or_create_user(user: CurrentUser) -> UserProfile:
    """Profiles are created lazily from the JWT claims the first time a user shows up."""
    user = await UserProfile.find_one(UserProfile.user_id == user.id, UserProfile.deleted_at == None)  # noqa: E711
    if user is None:
        user = UserProfile(user_id=user.id, email=user.emailid, role=user.role, active=True)
        try:
            await user.insert()
        except DuplicateKeyError:  # two first requests raced; the other one won
            user = await UserProfile.find_one(UserProfile.user_id == user.id)
            if user is None:
                raise
        return user
    if user.email != user.emailid or user.role != user.role:  # keep in sync with auth
        user.email, user.role = user.emailid, user.role
        user.updated_at = utcnow()
        await user.save()
    return user


async def _get_or_404(user_id: str) -> UserProfile:
    user = await UserProfile.find_one(UserProfile.user_id == user_id, UserProfile.deleted_at == None)  # noqa: E711
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "UserProfile not found")
    return user


# ---------- Any logged-in user: own profile ----------
# NOTE: "/me" routes are declared before "/{user_id}" so "me" is never read as an id.

@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(user: CurrentUser = Depends(get_current_user)):
    return await _get_or_create_user(user)


@router.patch("/me", response_model=UserProfileResponse)
async def update_my_profile(
    payload: UserProfileUpdate, user: CurrentUser = Depends(get_current_user)
):
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields to update")
    user = await _get_or_create_user(user)
    for field, value in changes.items():
        setattr(user, field, value)
    user.updated_at = utcnow()
    await user.save()
    return user


# ---------- Admin: view all users ----------

@router.get("/", response_model=list[UserProfileResponse])
async def list_users(
    response: Response,
    q: str | None = Query(None, min_length=1, max_length=100, description="Search name or email"),
    role: str | None = Query(None, description="Filter by role, e.g. admin or user"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _: CurrentUser = Depends(require_admin),
):
    conditions = [UserProfile.deleted_at == None]  # noqa: E711
    if q:
        pattern = re.escape(q)  # user input is matched literally, never as a regex
        conditions.append(
            Or(RegEx(UserProfile.full_name, pattern, "i"), RegEx(UserProfile.email, pattern, "i"))
        )
    if role:
        conditions.append(UserProfile.role == role)
    query = UserProfile.find(*conditions)
    response.headers["X-Total-Count"] = str(await query.count())
    return await query.sort("-created_at").skip(skip).limit(limit).to_list()


@router.post("/", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: AdminUserCreate, _: CurrentUser = Depends(require_admin)):
    account = await account_request("POST", "/internal/users", {
        "name": payload.name, "emailid": payload.email, "pass": payload.password,
        "mobile": payload.mobile, "role": payload.role,
    })
    user = UserProfile(
        **payload.model_dump(exclude={"name", "password", "mobile", "role"}),
        user_id=account["id"], email=account["emailid"], role=account["role"], active=account["active"],
        full_name=payload.full_name or payload.name,
        phone=payload.phone or payload.mobile,
    )
    await user.insert()
    return user


# ---------- Admin (any user) or the user themselves: view profile ----------

@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str, _: CurrentUser = Depends(require_self_or_admin)
):
    return await _get_or_404(user_id)


@router.patch("/{user_id}", response_model=UserProfileResponse)
async def update_user(
    user_id: str, payload: AdminUserUpdate, _: CurrentUser = Depends(require_admin)
):
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields to update")
    user = await _get_or_404(user_id)
    account_fields = {"email": "emailid", "mobile": "mobile", "role": "role", "active": "active"}
    account_changes = {account_fields[key]: value for key, value in changes.items() if key in account_fields}
    if account_changes:
        account = await account_request("PATCH", f"/internal/users/{user_id}", account_changes)
        user.email, user.role, user.active = account["emailid"], account["role"], account["active"]
    for field in {"full_name", "phone", "address", "date_of_birth"} & changes.keys():
        setattr(user, field, changes[field])
    user.updated_at = utcnow()
    await user.save()
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(user_id: str, _: CurrentUser = Depends(require_admin)):
    user = await _get_or_404(user_id)
    await account_request("PATCH", f"/internal/users/{user_id}", {"active": False})
    user.active = False
    user.deleted_at = utcnow()
    user.updated_at = utcnow()
    await user.save()
