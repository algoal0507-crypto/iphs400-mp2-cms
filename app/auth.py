"""Password hashing, signed session cookies, and CSRF tokens.

Session: a signed, timed token (itsdangerous) carrying the user id, stored in
an httponly cookie. Nothing about the session lives server-side, so there is
no session table to clean up.

CSRF: the double-submit cookie pattern. `new_csrf_token` + `set_csrf_cookie`
put a random value in a cookie *and* a hidden form field; `csrf_is_valid`
checks the two match. An attacker forging a cross-site POST cannot read the
cookie, so cannot supply a matching field.
"""
from __future__ import annotations

import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerificationError, VerifyMismatchError
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from starlette.requests import Request
from starlette.responses import Response

from app import settings

SESSION_COOKIE = "session"
SESSION_MAX_AGE = 60 * 60 * 8  # 8 hours
CSRF_COOKIE = "csrf_token"

_hasher = PasswordHasher()
_serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="session")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHash):
        return False


def set_session_cookie(response: Response, user_id: int) -> None:
    token = _serializer.dumps({"user_id": user_id})
    response.set_cookie(
        SESSION_COOKIE, token, max_age=SESSION_MAX_AGE,
        httponly=True, samesite="lax",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE)


def read_session(request: Request) -> int | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    try:
        data = _serializer.loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    return data.get("user_id")


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def set_csrf_cookie(response: Response, token: str) -> None:
    response.set_cookie(CSRF_COOKIE, token, httponly=True, samesite="lax")


def csrf_is_valid(request: Request, submitted: str | None) -> bool:
    cookie_value = request.cookies.get(CSRF_COOKIE)
    if not cookie_value or not submitted:
        return False
    return secrets.compare_digest(cookie_value, submitted)
