from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, Response, status
from sqlalchemy import select, update

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
from app.db import AsyncSessionLocal
from app.models.password_reset import PasswordReset
from app.models.refresh_token import RefreshToken
from app.models.user import User

SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_TOKEN_REMEMBER_DAYS: int = int(os.environ.get("REFRESH_TOKEN_REMEMBER_DAYS", "30"))
BCRYPT_ROUNDS: int = int(os.environ.get("BCRYPT_ROUNDS", "12"))
COOKIE_SECURE: bool = os.environ.get("COOKIE_SECURE", "false").lower() == "true"


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _generate_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _generate_refresh_token_value() -> str:
    return hashlib.sha256(os.urandom(64)).hexdigest()


def _decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )


def _set_refresh_cookie(response: Response, token: str, remember_me: bool) -> None:
    max_age = (
        REFRESH_TOKEN_REMEMBER_DAYS * 86400
        if remember_me
        else REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=max_age,
        path="/auth/refresh",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        path="/auth/refresh",
    )


class AuthService:
    async def register(self, body: RegisterRequest) -> RegisterResponse:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.email == body.email))
            existing = result.scalar_one_or_none()
            if existing is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "EMAIL_TAKEN",
                        "message": "An account with this email already exists.",
                        "details": {},
                    },
                )

            password_hash = bcrypt.hashpw(
                body.password.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
            ).decode()

            user = User(
                full_name=body.full_name,
                email=body.email,
                password_hash=password_hash,
                is_active=True,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return RegisterResponse(
            id=str(user.id),
            full_name=user.full_name,
            email=user.email,
            created_at=user.created_at.isoformat(),
        )

    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.email == body.email))
            user = result.scalar_one_or_none()

            invalid_exc = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                    "details": {},
                },
            )

            if user is None:
                raise invalid_exc

            if not bcrypt.checkpw(body.password.encode(), user.password_hash.encode()):
                raise invalid_exc

            if not user.is_active:
                raise invalid_exc

            access_token = _generate_access_token(user.id, user.email)

            raw_refresh = _generate_refresh_token_value()
            remember_me = body.remember_me if body.remember_me is not None else False
            expire_days = REFRESH_TOKEN_REMEMBER_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
            expires_at = datetime.now(timezone.utc) + timedelta(days=expire_days)

            refresh_record = RefreshToken(
                user_id=user.id,
                token_hash=_hash_token(raw_refresh),
                expires_at=expires_at,
                remember_me=remember_me,
            )
            session.add(refresh_record)
            await session.commit()

        _set_refresh_cookie(response, raw_refresh, remember_me)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def forgotPassword(self, body: ForgotPasswordRequest) -> ForgotPasswordResponse:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.email == body.email))
            user = result.scalar_one_or_none()

            if user is not None and user.is_active:
                raw_token = _generate_refresh_token_value()
                expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
                reset_record = PasswordReset(
                    user_id=user.id,
                    token_hash=_hash_token(raw_token),
                    expires_at=expires_at,
                )
                session.add(reset_record)
                await session.commit()
                # In a real system, send email with raw_token here.

        return ForgotPasswordResponse(
            message="If an account with that email exists, a password reset link has been sent."
        )

    async def resetPassword(self, body: ResetPasswordRequest) -> ResetPasswordResponse:
        token_hash = _hash_token(body.token)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PasswordReset).where(PasswordReset.token_hash == token_hash)
            )
            reset_record = result.scalar_one_or_none()

            invalid_exc = HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_RESET_TOKEN",
                    "message": "This password reset link is invalid or has expired.",
                    "details": {},
                },
            )

            if reset_record is None:
                raise invalid_exc

            if reset_record.used_at is not None:
                raise invalid_exc

            if reset_record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                raise invalid_exc

            user_result = await session.execute(
                select(User).where(User.id == reset_record.user_id)
            )
            user = user_result.scalar_one_or_none()
            if user is None:
                raise invalid_exc

            password_hash = bcrypt.hashpw(
                body.password.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
            ).decode()

            user.password_hash = password_hash
            reset_record.used_at = datetime.now(timezone.utc)
            session.add(user)
            session.add(reset_record)
            await session.commit()

        return ResetPasswordResponse(message="Your password has been reset successfully.")

    async def me(self, access_token: str) -> MeResponse:
        payload = _decode_access_token(access_token)
        user_id = payload.get("sub")

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        return MeResponse(
            id=str(user.id),
            full_name=user.full_name,
            email=user.email,
            created_at=user.created_at.isoformat(),
        )

    async def logout(
        self,
        access_token: Optional[str],
        refresh_token: Optional[str],
        response: Response,
    ) -> LogoutResponse:
        if refresh_token is not None:
            token_hash = _hash_token(refresh_token)
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(RefreshToken).where(RefreshToken.token_hash == token_hash)
                )
                record = result.scalar_one_or_none()
                if record is not None and record.revoked_at is None:
                    record.revoked_at = datetime.now(timezone.utc)
                    session.add(record)
                    await session.commit()

        _clear_refresh_cookie(response)

        return LogoutResponse(message="Logged out successfully.")

    async def refresh(
        self,
        refresh_token: Optional[str],
        response: Response,
    ) -> RefreshResponse:
        invalid_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_REFRESH_TOKEN",
                "message": "Session expired. Please log in again.",
                "details": {},
            },
        )

        if refresh_token is None:
            raise invalid_exc

        token_hash = _hash_token(refresh_token)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(RefreshToken).where(RefreshToken.token_hash == token_hash)
            )
            record = result.scalar_one_or_none()

            if record is None:
                raise invalid_exc

            if record.revoked_at is not None:
                raise invalid_exc

            if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                raise invalid_exc

            user_result = await session.execute(
                select(User).where(User.id == record.user_id)
            )
            user = user_result.scalar_one_or_none()

            if user is None or not user.is_active:
                raise invalid_exc

            # Revoke old token
            record.revoked_at = datetime.now(timezone.utc)
            session.add(record)

            # Issue new refresh token
            raw_refresh = _generate_refresh_token_value()
            remember_me = record.remember_me
            expire_days = REFRESH_TOKEN_REMEMBER_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
            expires_at = datetime.now(timezone.utc) + timedelta(days=expire_days)

            new_record = RefreshToken(
                user_id=user.id,
                token_hash=_hash_token(raw_refresh),
                expires_at=expires_at,
                remember_me=remember_me,
            )
            session.add(new_record)
            await session.commit()

        access_token = _generate_access_token(user.id, user.email)
        _set_refresh_cookie(response, raw_refresh, remember_me)

        return RefreshResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
