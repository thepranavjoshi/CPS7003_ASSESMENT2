from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from dal.models import User
from security.passwords import verify_password
from security.rbac import Actor

class AuthenticationError(Exception):
    pass

def authenticate(session: Session, username: str, password: str) -> Actor:
    user = session.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid username or password")
    return Actor(username=user.username, role=user.role)
