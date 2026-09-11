from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    MeResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.database import get_session
from app.models import PasswordReset, RefreshToken, User

# ---------------------------------------------------------------------------
# Configuration (read from environment with sane defaults)
# ---------------------------------------------------------------------------
SECRET_KEY: str = os.environ.get("SECRET_KEY", "change-me-in-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_TOKEN_REMEMBER_ME_DAYS: int = int(os.environ.get("REFRESH_TOKEN_REMEMBER_ME_DAYS", "30"))
BCRYPT_ROUNDS: int = int(os.environ.get("BCRYPT_ROUNDS", "12"))
PASSWORD_RESET_EXPIRE_HOURS: int = int(os.environ.get("PASSWORD_RESET_EXPIRE_HOURS", "1"))
REFRESH_COOKIE_NAME: str = "refresh_token"

# ---------------------------------------------------------------------------
# Rate limiting (simple in-memory; replace with Redis in production)
# ---------------------------------------------------------------------------
from collections import defaultdict
import time

_login_attempts: dict[str, list[float]] = defaultdict(list)
_forgot_attempts: dict[str, list[float]] = defaultdict(list)

LOGIN_RATE_LIMIT: int = int(os.environ.get("LOGIN_RATE_LIMIT", "5"))
LOGIN_RATE_WINDOW: int = int(os.environ.get("LOGIN_RATE_WINDOW", "60"))
FORGOT_RATE_LIMIT: int = int(os.environ.get("FORGOT_RATE_LIMIT", "3"))
FORGOT_RATE_WINDOW: int = int(os.environ.get("FORGOT_RATE_WINDOW", "300"))


def _check_rate_limit(
    store: dict[str, list[float]],
    key: str,
    limit: int,
    window: int,
) -> None:
    now = time.monotonic()
    attempts = [t for t in store[key] if now - t < window]
    attempts.append(now)
    store[key] = attempts
    if len(attempts) > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": {
                    "code": "RATE_LIMITED",
                    "message": "Too many attempts. Please try again later.",
                    "details": {},
                }
            },
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _create_access_token(user_id: str, email: str) -> str:
    expire = _now_utc() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": _now_utc(),
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "TOKEN_EXPIRED",
                    "message": "Token has expired.",
                    "details": {},
                }
            },
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "Invalid token.",
                    "details": {},
                }
            },
        )


def _set_refresh_cookie(response: Response, token: str, remember_me: bool) -> None:
    max_age = (
        REFRESH_TOKEN_REMEMBER_ME_DAYS * 86400 if remember_me else REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=os.environ.get("SECURE_COOKIES", "true").lower() == "true",
        max_age=max_age,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/")


def _validate_password_policy(password: str) -> Optional[str]:
    """Return an error message if password violates policy, else None."""
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one number."
    return None


async def _get_session() -> AsyncSession:
    """Dependency-free session factory for service-layer use."""
    async for session in get_session():
        return session
    raise RuntimeError("Could not obtain database session")


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------

async def login(body: LoginRequest, response: Response, request: Request) -> LoginResponse:
    client_ip: str = request.client.host if request.client else "unknown"
    _check_rate_limit(_login_attempts, client_ip, LOGIN_RATE_LIMIT, LOGIN_RATE_WINDOW)

    _invalid_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password.",
                "details": {},
            }
        },
    )

    session: AsyncSession = await _get_session()
    async with session:
        result = await session.execute(select(User).where(User.email == body.email))
        user: Optional[User] = result.scalar_one_or_none()

        if user is None or not _verify_password(body.password, user.password_hash):
            raise _invalid_exc

        if not user.is_active:
            raise _invalid_exc

        # Rotate refresh token
        remember_me: bool = body.remember_me if body.remember_me is not None else False
        raw_refresh = secrets.token_urlsafe(64)
        token_hash = _sha256(raw_refresh)
        expire_days = REFRESH_TOKEN_REMEMBER_ME_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
        expires_at = _now_utc() + timedelta(days=expire_days)

        refresh_token_row = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            remember_me=remember_me,
            revoked_at=None,
        )
        session.add(refresh_token_row)
        await session.commit()
        await session.refresh(refresh_token_row)

    access_token = _create_access_token(user_id=str(user.id), email=user.email)
    _set_refresh_cookie(response, raw_refresh, remember_me)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=MeResponse(
            id=str(user.id),
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
    )


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------

async def register(body: RegisterRequest, response: Response, request: Request) -> RegisterResponse:
    policy_error = _validate_password_policy(body.password)
    if policy_error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "WEAK_PASSWORD",
                    "message": policy_error,
                    "details": {},
                }
            },
        )

    if body.password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "PASSWORD_MISMATCH",
                    "message": "Passwords do not match.",
                    "details": {},
                }
            },
        )

    session: AsyncSession = await _get_session()
    async with session:
        result = await session.execute(select(User).where(User.email == body.email))
        existing: Optional[User] = result.scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "EMAIL_TAKEN",
                        "message": "An account with this email already exists.",
                        "details": {},
                    }
                },
            )

        password_hash = _hash_password(body.password)
        user = User(
            full_name=body.full_name,
            email=body.email,
            password_hash=password_hash,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    access_token = _create_access_token(user_id=str(user.id), email=user.email)

    raw_refresh = secrets.token_urlsafe(64)
    token_hash = _sha256(raw_refresh)
    expires_at = _now_utc() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    session2: AsyncSession = await _get_session()
    async with session2:
        refresh_token_row = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            remember_me=False,
            revoked_at=None,
        )
        session2.add(refresh_token_row)
        await session2.commit()

    _set_refresh_cookie(response, raw_refresh, remember_me=False)

    return RegisterResponse(
        access_token=access_token,
        token_type="bearer",
        user=MeResponse(
            id=str(user.id),
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
    )


# ---------------------------------------------------------------------------
# forgotPassword
# ---------------------------------------------------------------------------

async def forgotPassword(body: ForgotPasswordRequest, request: Request) -> ForgotPasswordResponse:
    client_ip: str = request.client.host if request.client else "unknown"
    _check_rate_limit(_forgot_attempts, client_ip, FORGOT_RATE_LIMIT, FORGOT_RATE_WINDOW)

    # Enumeration resistance: always return the same message
    _generic_response = ForgotPasswordResponse(
        message="If that email is registered, a reset link has been sent."
    )

    session: AsyncSession = await _get_session()
    async with session:
        result = await session.execute(select(User).where(User.email == body.email))
        user: Optional[User] = result.scalar_one_or_none()
        if user is None or not user.is_active:
            return _generic_response

        raw_token = secrets.token_urlsafe(64)
        token_hash = _sha256(raw_token)
        expires_at = _now_utc() + timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS)

        reset_row = PasswordReset(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            used_at=None,
        )
        session.add(reset_row)
        await session.commit()

    # In production, send raw_token via email. Intentionally not implemented here.
    return _generic_response


# ---------------------------------------------------------------------------
# resetPassword
# ---------------------------------------------------------------------------

async def resetPassword(body: ResetPasswordRequest) -> ResetPasswordResponse:
    if body.password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "PASSWORD_MISMATCH",
                    "message": "Passwords do not match.",
                    "details": {},
                }
            },
        )

    policy_error = _validate_password_policy(body.password)
    if policy_error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "WEAK_PASSWORD",
                    "message": policy_error,
                    "details": {},
                }
            },
        )

    token_hash = _sha256(body.token)
    now = _now_utc()

    _invalid_exc = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": {
                "code": "INVALID_OR_EXPIRED_TOKEN",
                "message": "This reset link is invalid or has expired.",
                "details": {},
            }
        },
    )

    session: AsyncSession = await _get_session()
    async with session:
        result = await session.execute(
            select(PasswordReset).where(
                PasswordReset.token_hash == token_hash,
                PasswordReset.used_at.is_(None),
                PasswordReset.expires_at > now,
            )
        )
        reset_row: Optional[PasswordReset] = result.scalar_one_or_none()
        if reset_row is None:
            raise _invalid_exc

        user_result = await session.execute(select(User).where(User.id == reset_row.user_id))
        user: Optional[User] = user_result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise _invalid_exc

        user.password_hash = _hash_password(body.password)
        reset_row.used_at = now

        # Revoke all active refresh tokens for the user
        await session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

        await session.commit()

    return ResetPasswordResponse(message="Your password has been reset successfully.")


# ---------------------------------------------------------------------------
# me
# ---------------------------------------------------------------------------

async def me(request: Request) -> MeResponse:
    auth_header: Optional[str] = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "MISSING_TOKEN",
                    "message": "Authentication required.",
                    "details": {},
                }
            },
        )
    token = auth_header.split(" ", 1)[1]
    payload = _decode_access_token(token)
    user_id: str = payload["sub"]

    session: AsyncSession = await _get_session()
    async with session:
        result = await session.execute(select(User).where(User.id == user_id))
        user: Optional[User] = result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "USER_NOT_FOUND",
                        "message": "User not found.",
                        "details": {},
                    }
                },
            )

    return MeResponse(
        id=str(user.id),
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
    )


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------

async def logout(request: Request, response: Response) -> LogoutResponse:
    raw_refresh: Optional[str] = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_refresh:
        token_hash = _sha256(raw_refresh)
        now = _now_utc()
        session: AsyncSession = await _get_session()
        async with session:
            await session.execute(
                update(RefreshToken)
                .where(
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.revoked_at.is_(None),
                )
                .values(revoked_at=now)
            )
            await session.commit()

    _clear_refresh_cookie(response)
    return LogoutResponse(message="Logged out successfully.")


# ---------------------------------------------------------------------------
# refresh
# ---------------------------------------------------------------------------

async def refresh(request: Request, response: Response) -> RefreshResponse:
    raw_refresh: Optional[str] = request.cookies.get(REFRESH_COOKIE_NAME)
    _invalid_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": "INVALID_REFRESH_TOKEN",
                "message": "Invalid or expired refresh token.",
                "details": {},
            }
        },
    )

    if not raw_refresh:
        raise _invalid_exc

    token_hash = _sha256(raw_refresh)
    now = _now_utc()

    session: AsyncSession = await _get_session()
    async with session:
        result = await session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now,
            )
        )
        token_row: Optional[RefreshToken] = result.scalar_one_or_none()
        if token_row is None:
            raise _invalid_exc

        user_result = await session.execute(select(User).where(User.id == token_row.user_id))
        user: Optional[User] = user_result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise _invalid_exc

        # Rotate: revoke old, issue new
        token_row.revoked_at = now

        remember_me: bool = token_row.remember_me
        raw_new = secrets.token_urlsafe(64)
        new_hash = _sha256(raw_new)
        expire_days = REFRESH_TOKEN_REMEMBER_ME_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
        new_expires_at = now + timedelta(days=expire_days)

        new_token_row = RefreshToken(
            user_id=user.id,
            token_hash=new_hash,
            expires_at=new_expires_at,
            remember_me=remember_me,
            revoked_at=None,
        )
        session.add(new_token_row)
        await session.commit()

    access_token = _create_access_token(user_id=str(user.id), email=user.email)
    _set_refresh_cookie(response, raw_new, remember_me)

    return RefreshResponse(
        access_token=access_token,
        token_type="bearer",
    )
