from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import CurrentUser, decode_access_token

bearer_scheme = HTTPBearer()


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    return decode_access_token(creds.credentials)


def require_roles(*roles: str):
    def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin permission required")
        return user

    return checker


require_admin = require_roles("admin")


def require_self_or_admin(
    user_id: str, user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """For /{user_id} routes: a member may read their own data, an admin anyone's."""
    if user.role != "admin" and user.id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only access your own data")
    return user
