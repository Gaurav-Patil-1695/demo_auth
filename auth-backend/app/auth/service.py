from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    MeResponse,
    LogoutResponse,
    RefreshResponse,
)
from app.db import get_db
from app.models import User, PasswordReset, RefreshToken


BCRYPT_ROUNDS: int = int(os.environ.get("BCRYPT_ROUNDS", "12"))
JWT_SECRET: str = os.environ.get("JWT_SECRET", "changeme")
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
)
REFRESH_TOKEN_EXPIRE_DAYS: int = int(
    os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7")
)
REFRESH_TOKEN_REMEMBER_ME_EXPIRE_DAYS: int = int(
    os.environ.get("REFRESH_TOKEN_REMEMBER_ME_EXPIRE_DAYS", "30")
)
PASSWORD_RESET_EXPIRE_MINUTES: int = int(
    os.environ.get("PASSWORD_RESET_EXPIRE_MINUTES", "60")
)


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _validate_password_strength(password: str) -> Optional[str]:
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one number."
    return None


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def register(self, payload: RegisterRequest) -> RegisterResponse:
        # Validate password strength
        strength_error = _validate_password_strength(payload.password)
        if strength_error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "WEAK_PASSWORD",
                        "message": strength_error,
                        "details": None,
                    }
                },
            )

        # Validate confirm_password
        if payload.password != payload.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "PASSWORD_MISMATCH",
                        "message": "Passwords do not match.",
                        "details": None,
                    }
                },
            )

        # Check duplicate email
        result = await self._db.execute(
            select(User).where(User.email == payload.email.lower())
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "EMAIL_TAKEN",
                        "message": "An account with this email already exists.",
                        "details": None,
                    }
                },
            )

        password_hash = _hash_password(payload.password)
        now = datetime.now(timezone.utc)
        user = User(
            id=str(uuid.uuid4()),
            full_name=payload.full_name,
            email=payload.email.lower(),
            password_hash=password_hash,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)

        access_token = _create_access_token(user.id)
        refresh_token_plain = str(uuid.uuid4())
        refresh_token_hash = _sha256(refresh_token_plain)
        expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        rt = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=expires_at,
            revoked_at=None,
            remember_me=False,
            created_at=now,
        )
        self._db.add(rt)
        await self._db.commit()

        return RegisterResponse(
            access_token=access_token,
            refresh_token=refresh_token_plain,
            token_type="bearer",
            user=MeResponse(
                id=user.id,
                full_name=user.full_name,
                email=user.email,
                is_active=user.is_active,
                created_at=user.created_at,
            ),
        )

    async def login(self, payload: LoginRequest) -> LoginResponse:
        result = await self._db.execute(
            select(User).where(User.email == payload.email.lower())
        )
        user = result.scalar_one_or_none()

        if user is None or not _verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid email or password.",
                        "details": None,
                    }
                },
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "ACCOUNT_INACTIVE",
                        "message": "Your account is inactive.",
                        "details": None,
                    }
                },
            )

        now = datetime.now(timezone.utc)
        access_token = _create_access_token(user.id)
        refresh_token_plain = str(uuid.uuid4())
        refresh_token_hash = _sha256(refresh_token_plain)
        remember_me: bool = getattr(payload, "remember_me", False) or False
        days = REFRESH_TOKEN_REMEMBER_ME_EXPIRE_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
        expires_at = now + timedelta(days=days)
        rt = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=expires_at,
            revoked_at=None,
            remember_me=remember_me,
            created_at=now,
        )
        self._db.add(rt)
        await self._db.commit()

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token_plain,
            token_type="bearer",
            user=MeResponse(
                id=user.id,
                full_name=user.full_name,
                email=user.email,
                is_active=user.is_active,
                created_at=user.created_at,
            ),
        )

    async def forgot_password(self, payload: ForgotPasswordRequest) -> ForgotPasswordResponse:
        result = await self._db.execute(
            select(User).where(User.email == payload.email.lower())
        )
        user = result.scalar_one_or_none()

        if user is not None and user.is_active:
            now = datetime.now(timezone.utc)
            token_plain = str(uuid.uuid4())
            token_hash = _sha256(token_plain)
            expires_at = now + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
            pr = PasswordReset(
                id=str(uuid.uuid4()),
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
                used_at=None,
                created_at=now,
            )
            self._db.add(pr)
            await self._db.commit()
            # In a real app, send token_plain via email here.

        return ForgotPasswordResponse(
            message="If that email address is in our system, you will receive a password reset email."
        )

    async def reset_password(self, payload: ResetPasswordRequest) -> ResetPasswordResponse:
        token_hash = _sha256(payload.token)
        now = datetime.now(timezone.utc)
        result = await self._db.execute(
            select(PasswordReset).where(
                PasswordReset.token_hash == token_hash,
                PasswordReset.used_at.is_(None),
                PasswordReset.expires_at > now,
            )
        )
        pr = result.scalar_one_or_none()
        if pr is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_RESET_TOKEN",
                        "message": "This password reset link is invalid or has expired.",
                        "details": None,
                    }
                },
            )

        strength_error = _validate_password_strength(payload.password)
        if strength_error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "WEAK_PASSWORD",
                        "message": strength_error,
                        "details": None,
                    }
                },
            )

        if payload.password != payload.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "PASSWORD_MISMATCH",
                        "message": "Passwords do not match.",
                        "details": None,
                    }
                },
            )

        new_hash = _hash_password(payload.password)
        await self._db.execute(
            update(User)
            .where(User.id == pr.user_id)
            .values(password_hash=new_hash, updated_at=now)
        )
        pr.used_at = now
        await self._db.commit()

        return ResetPasswordResponse(message="Your password has been reset successfully.")

    async def me(self) -> MeResponse:
        # Caller must inject the current user; placeholder raises 501.
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "error": {
                    "code": "NOT_IMPLEMENTED",
                    "message": "Dependency injection for current user required.",
                    "details": None,
                }
            },
        )

    async def logout(self) -> LogoutResponse:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "error": {
                    "code": "NOT_IMPLEMENTED",
                    "message": "Dependency injection for current user required.",
                    "details": None,
                }
            },
        )

    async def refresh(self) -> RefreshResponse:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "error": {
                    "code": "NOT_IMPLEMENTED",
                    "message": "Dependency injection for refresh token required.",
                    "details": None,
                }
            },
        )


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)
