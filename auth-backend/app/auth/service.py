from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Response

from app.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    MeResponse,
    LogoutRequest,
    LogoutResponse,
    RefreshRequest,
    RefreshResponse,
)
from app.auth.repository import AuthRepository
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_token,
    generate_token,
)
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    ValidationError,
    NotFoundError,
)
from app.models.user import User


class AuthService:
    def __init__(self, repository: AuthRepository) -> None:
        self._repo = repository

    async def register(self, body: RegisterRequest) -> RegisterResponse:
        existing = await self._repo.get_user_by_email(body.email)
        if existing is not None:
            raise ConflictError(
                code="EMAIL_ALREADY_REGISTERED",
                message="An account with this email address already exists.",
            )

        if body.password != body.confirm_password:
            raise ValidationError(
                code="PASSWORD_MISMATCH",
                message="Passwords do not match.",
            )

        password_hash = hash_password(body.password)
        user = await self._repo.create_user(
            full_name=body.full_name,
            email=body.email,
            password_hash=password_hash,
        )

        return RegisterResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        user = await self._repo.get_user_by_email(body.email)
        if user is None or not verify_password(body.password, user.password_hash):
            raise AuthenticationError(
                code="INVALID_CREDENTIALS",
                message="Invalid email or password.",
            )

        if not user.is_active:
            raise AuthenticationError(
                code="ACCOUNT_INACTIVE",
                message="Invalid email or password.",
            )

        access_token = create_access_token(subject=str(user.id))

        raw_refresh_token = generate_token()
        token_hash = hash_token(raw_refresh_token)
        remember_me: bool = body.remember_me if body.remember_me is not None else False
        refresh_expires = timedelta(
            days=settings.REFRESH_TOKEN_REMEMBER_DAYS
            if remember_me
            else settings.REFRESH_TOKEN_DAYS
        )
        expires_at = datetime.now(timezone.utc) + refresh_expires

        await self._repo.create_refresh_token(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            remember_me=remember_me,
        )

        response.set_cookie(
            key="refresh_token",
            value=raw_refresh_token,
            httponly=True,
            samesite="lax",
            secure=settings.COOKIE_SECURE,
            max_age=int(refresh_expires.total_seconds()),
            path="/auth",
        )

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
        )

    async def forgotPassword(self, body: ForgotPasswordRequest) -> ForgotPasswordResponse:
        user = await self._repo.get_user_by_email(body.email)
        if user is not None and user.is_active:
            raw_token = generate_token()
            token_hash = hash_token(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
            )
            await self._repo.create_password_reset(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            # In a real system, the reset link would be emailed here.
            # Email sending is outside the scope of this service layer.

        return ForgotPasswordResponse(
            message="If an account with that email exists, a password reset link has been sent."
        )

    async def resetPassword(self, body: ResetPasswordRequest) -> ResetPasswordResponse:
        if body.password != body.confirm_password:
            raise ValidationError(
                code="PASSWORD_MISMATCH",
                message="Passwords do not match.",
            )

        token_hash = hash_token(body.token)
        reset_record = await self._repo.get_valid_password_reset(token_hash=token_hash)

        if reset_record is None:
            raise ValidationError(
                code="INVALID_OR_EXPIRED_TOKEN",
                message="This password reset link is invalid or has expired.",
            )

        new_password_hash = hash_password(body.password)
        await self._repo.update_user_password(
            user_id=reset_record.user_id,
            password_hash=new_password_hash,
        )
        await self._repo.mark_password_reset_used(reset_id=reset_record.id)
        await self._repo.revoke_all_refresh_tokens(user_id=reset_record.user_id)

        return ResetPasswordResponse(
            message="Your password has been reset successfully. Please log in with your new password."
        )

    async def me(self, current_user: User) -> MeResponse:
        return MeResponse(
            id=current_user.id,
            full_name=current_user.full_name,
            email=current_user.email,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
        )

    async def logout(self, body: LogoutRequest, response: Response) -> LogoutResponse:
        if body.refresh_token is not None:
            token_hash = hash_token(body.refresh_token)
            await self._repo.revoke_refresh_token(token_hash=token_hash)

        response.delete_cookie(key="refresh_token", path="/auth")

        return LogoutResponse(message="Logged out successfully.")

    async def refresh(self, body: RefreshRequest, response: Response) -> RefreshResponse:
        raw_token: Optional[str] = body.refresh_token
        if not raw_token:
            raise AuthenticationError(
                code="MISSING_REFRESH_TOKEN",
                message="Refresh token is required.",
            )

        token_hash = hash_token(raw_token)
        record = await self._repo.get_valid_refresh_token(token_hash=token_hash)

        if record is None:
            raise AuthenticationError(
                code="INVALID_REFRESH_TOKEN",
                message="Refresh token is invalid or has expired.",
            )

        await self._repo.revoke_refresh_token(token_hash=token_hash)

        user = await self._repo.get_user_by_id(record.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError(
                code="ACCOUNT_INACTIVE",
                message="Invalid email or password.",
            )

        access_token = create_access_token(subject=str(user.id))

        new_raw_refresh_token = generate_token()
        new_token_hash = hash_token(new_raw_refresh_token)
        remember_me: bool = record.remember_me
        refresh_expires = timedelta(
            days=settings.REFRESH_TOKEN_REMEMBER_DAYS
            if remember_me
            else settings.REFRESH_TOKEN_DAYS
        )
        expires_at = datetime.now(timezone.utc) + refresh_expires

        await self._repo.create_refresh_token(
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=expires_at,
            remember_me=remember_me,
        )

        response.set_cookie(
            key="refresh_token",
            value=new_raw_refresh_token,
            httponly=True,
            samesite="lax",
            secure=settings.COOKIE_SECURE,
            max_age=int(refresh_expires.total_seconds()),
            path="/auth",
        )

        return RefreshResponse(
            access_token=access_token,
            token_type="bearer",
        )
