import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import HTTPException, Request, Response, status
from jose import JWTError, jwt

from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    MeResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.models.password_reset import PasswordReset

# ---------------------------------------------------------------------------
# Environment-driven configuration
# ---------------------------------------------------------------------------
SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "changeme-secret-key")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_TOKEN_REMEMBER_ME_DAYS: int = int(os.environ.get("REFRESH_TOKEN_REMEMBER_ME_DAYS", "30"))
BCRYPT_ROUNDS: int = int(os.environ.get("BCRYPT_ROUNDS", "12"))
RESET_TOKEN_EXPIRE_MINUTES: int = 30
REFRESH_COOKIE_NAME: str = "refresh_token"

# ---------------------------------------------------------------------------
# In-memory stores (replace with real DB repositories in production)
# ---------------------------------------------------------------------------
# users: dict keyed by email -> {id, full_name, email, password_hash, is_active, created_at, updated_at}
_users: dict = {}
# refresh_tokens: dict keyed by token_hash -> {id, user_id, token_hash, expires_at, revoked_at, remember_me, created_at}
_refresh_tokens: dict = {}
# password_resets: dict keyed by token_hash -> PasswordReset
_password_resets: dict = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _create_access_token(user_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Authentication required.",
                    "details": [],
                }
            },
        )


def _set_refresh_cookie(response: Response, token: str, remember_me: bool) -> None:
    max_age = (
        REFRESH_TOKEN_REMEMBER_ME_DAYS * 86400
        if remember_me
        else REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=max_age,
        path="/auth/refresh",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/auth/refresh",
    )


def _validate_password_policy(password: str) -> list:
    """Return list of validation error detail dicts if policy not met."""
    errors = []
    if len(password) < 8:
        errors.append({"field": "password", "message": "Password must be at least 8 characters."})
    if not any(c.isupper() for c in password):
        errors.append({"field": "password", "message": "Password must contain at least one uppercase letter."})
    if not any(c.islower() for c in password):
        errors.append({"field": "password", "message": "Password must contain at least one lowercase letter."})
    if not any(c.isdigit() for c in password):
        errors.append({"field": "password", "message": "Password must contain at least one number."})
    return errors


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class AuthService:
    # ------------------------------------------------------------------
    # login
    # ------------------------------------------------------------------
    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        user = _users.get(body.email)
        if not user or not _verify_password(body.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid email or password.",
                        "details": [],
                    }
                },
            )
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "ACCOUNT_INACTIVE",
                        "message": "Invalid email or password.",
                        "details": [],
                    }
                },
            )

        access_token = _create_access_token(user["id"], user["email"])
        raw_refresh = secrets.token_hex(32)
        token_hash = _sha256_hex(raw_refresh)
        remember_me: bool = getattr(body, "rememberMe", False) or False
        expire_days = REFRESH_TOKEN_REMEMBER_ME_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
        now = datetime.now(timezone.utc)
        _refresh_tokens[token_hash] = {
            "id": secrets.token_hex(16),
            "user_id": user["id"],
            "token_hash": token_hash,
            "expires_at": now + timedelta(days=expire_days),
            "revoked_at": None,
            "remember_me": remember_me,
            "created_at": now,
        }
        _set_refresh_cookie(response, raw_refresh, remember_me)

        return LoginResponse(
            accessToken=access_token,
            tokenType="bearer",
        )

    # ------------------------------------------------------------------
    # register
    # ------------------------------------------------------------------
    async def register(self, body: RegisterRequest) -> RegisterResponse:
        if body.email in _users:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "EMAIL_TAKEN",
                        "message": "An account with this email already exists.",
                        "details": [{"field": "email", "message": "An account with this email already exists."}],
                    }
                },
            )

        policy_errors = _validate_password_policy(body.password)
        if policy_errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Validation failed.",
                        "details": policy_errors,
                    }
                },
            )

        if body.password != body.confirmPassword:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Validation failed.",
                        "details": [{"field": "confirmPassword", "message": "Passwords do not match."}],
                    }
                },
            )

        now = datetime.now(timezone.utc)
        user_id = secrets.token_hex(16)
        _users[body.email] = {
            "id": user_id,
            "full_name": body.fullName,
            "email": body.email,
            "password_hash": _hash_password(body.password),
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }

        return RegisterResponse(
            message="Registration successful.",
        )

    # ------------------------------------------------------------------
    # forgotPassword
    # ------------------------------------------------------------------
    async def forgotPassword(self, body: ForgotPasswordRequest) -> ForgotPasswordResponse:
        # Enumeration resistance: always return the same response
        user = _users.get(body.email)
        if user and user["is_active"]:
            raw_token = secrets.token_hex(32)
            token_hash = _sha256_hex(raw_token)
            now = datetime.now(timezone.utc)
            pr = PasswordReset(
                id=secrets.token_hex(16),
                user_id=user["id"],
                token_hash=token_hash,
                expires_at=now + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES),
                used_at=None,
                created_at=now,
            )
            _password_resets[token_hash] = pr
            # In production, send raw_token via email here

        return ForgotPasswordResponse(
            message="If an account with that email exists, a password reset link has been sent.",
        )

    # ------------------------------------------------------------------
    # resetPassword
    # ------------------------------------------------------------------
    async def resetPassword(self, body: ResetPasswordRequest) -> ResetPasswordResponse:
        token_hash = _sha256_hex(body.token)
        pr: Optional[PasswordReset] = _password_resets.get(token_hash)

        if pr is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_RESET_TOKEN",
                        "message": "This password reset link is invalid or has expired.",
                        "details": [],
                    }
                },
            )

        now = datetime.now(timezone.utc)

        if pr.used_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_RESET_TOKEN",
                        "message": "This password reset link is invalid or has expired.",
                        "details": [],
                    }
                },
            )

        expires_at = pr.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now > expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_RESET_TOKEN",
                        "message": "This password reset link is invalid or has expired.",
                        "details": [],
                    }
                },
            )

        policy_errors = _validate_password_policy(body.password)
        if policy_errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Validation failed.",
                        "details": policy_errors,
                    }
                },
            )

        if body.password != body.confirmPassword:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Validation failed.",
                        "details": [{"field": "confirmPassword", "message": "Passwords do not match."}],
                    }
                },
            )

        # Find user and update password
        user = None
        for u in _users.values():
            if u["id"] == pr.user_id:
                user = u
                break

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_RESET_TOKEN",
                        "message": "This password reset link is invalid or has expired.",
                        "details": [],
                    }
                },
            )

        user["password_hash"] = _hash_password(body.password)
        user["updated_at"] = now

        # Mark token as used
        pr.used_at = now
        _password_resets[token_hash] = pr

        # Revoke all existing refresh tokens for this user
        for rt in _refresh_tokens.values():
            if rt["user_id"] == pr.user_id and rt["revoked_at"] is None:
                rt["revoked_at"] = now

        return ResetPasswordResponse(
            message="Your password has been reset successfully.",
        )

    # ------------------------------------------------------------------
    # me
    # ------------------------------------------------------------------
    async def me(self, token: str) -> MeResponse:
        payload = _decode_access_token(token)
        user_id = payload.get("sub")
        email = payload.get("email")
        user = _users.get(email)
        if not user or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required.",
                        "details": [],
                    }
                },
            )
        return MeResponse(
            id=user["id"],
            fullName=user["full_name"],
            email=user["email"],
            isActive=user["is_active"],
            createdAt=user["created_at"].isoformat(),
        )

    # ------------------------------------------------------------------
    # logout
    # ------------------------------------------------------------------
    async def logout(
        self,
        token: Optional[str],
        request: Request,
        response: Response,
    ) -> LogoutResponse:
        raw_refresh = request.cookies.get(REFRESH_COOKIE_NAME)
        if raw_refresh:
            token_hash = _sha256_hex(raw_refresh)
            rt = _refresh_tokens.get(token_hash)
            if rt and rt["revoked_at"] is None:
                rt["revoked_at"] = datetime.now(timezone.utc)
        _clear_refresh_cookie(response)
        return LogoutResponse(message="Logged out successfully.")

    # ------------------------------------------------------------------
    # refresh
    # ------------------------------------------------------------------
    async def refresh(self, request: Request, response: Response) -> RefreshResponse:
        raw_refresh = request.cookies.get(REFRESH_COOKIE_NAME)
        if not raw_refresh:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required.",
                        "details": [],
                    }
                },
            )

        token_hash = _sha256_hex(raw_refresh)
        rt = _refresh_tokens.get(token_hash)

        if rt is None or rt["revoked_at"] is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required.",
                        "details": [],
                    }
                },
            )

        now = datetime.now(timezone.utc)
        expires_at = rt["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now > expires_at:
            rt["revoked_at"] = now
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required.",
                        "details": [],
                    }
                },
            )

        # Find user
        user = None
        for u in _users.values():
            if u["id"] == rt["user_id"]:
                user = u
                break

        if user is None or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required.",
                        "details": [],
                    }
                },
            )

        # Rotate refresh token
        rt["revoked_at"] = now
        new_raw_refresh = secrets.token_hex(32)
        new_token_hash = _sha256_hex(new_raw_refresh)
        remember_me: bool = rt.get("remember_me", False)
        expire_days = REFRESH_TOKEN_REMEMBER_ME_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
        _refresh_tokens[new_token_hash] = {
            "id": secrets.token_hex(16),
            "user_id": user["id"],
            "token_hash": new_token_hash,
            "expires_at": now + timedelta(days=expire_days),
            "revoked_at": None,
            "remember_me": remember_me,
            "created_at": now,
        }
        _set_refresh_cookie(response, new_raw_refresh, remember_me)

        new_access_token = _create_access_token(user["id"], user["email"])
        return RefreshResponse(
            accessToken=new_access_token,
            tokenType="bearer",
        )
