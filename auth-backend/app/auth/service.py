import hashlib
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, Request, Response, status

from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    MeResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    LogoutResponse,
)

# ---------------------------------------------------------------------------
# Environment-driven configuration
# ---------------------------------------------------------------------------
SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
)
REFRESH_TOKEN_EXPIRE_DAYS: int = int(
    os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7")
)
REFRESH_TOKEN_REMEMBER_DAYS: int = int(
    os.environ.get("REFRESH_TOKEN_REMEMBER_DAYS", "30")
)
BCRYPT_ROUNDS: int = int(os.environ.get("BCRYPT_ROUNDS", "12"))
COOKIE_SECURE: bool = os.environ.get("COOKIE_SECURE", "true").lower() == "true"

# In-memory stores (replace with real DB repositories in production)
_users: dict[str, dict] = {}          # email -> user record
_refresh_tokens: dict[str, dict] = {} # token_hash -> token record
_password_resets: dict[str, dict] = {} # token_hash -> reset record


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _create_refresh_token() -> str:
    return hashlib.sha256(os.urandom(64)).hexdigest()


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
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=max_age,
        path="/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/auth",
    )


def _decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "TOKEN_EXPIRED",
                    "message": "Access token has expired.",
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
                    "message": "Invalid access token.",
                    "details": {},
                }
            },
        )


class AuthService:
    # ------------------------------------------------------------------
    # register
    # ------------------------------------------------------------------
    async def register(
        self, body: RegisterRequest, response: Response
    ) -> RegisterResponse:
        if body.email in _users:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "EMAIL_ALREADY_REGISTERED",
                        "message": "An account with this email already exists.",
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

        user_id = hashlib.sha256(body.email.encode()).hexdigest()[:32]
        now = datetime.now(timezone.utc)
        user = {
            "id": user_id,
            "full_name": body.full_name,
            "email": body.email,
            "password_hash": _hash_password(body.password),
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        _users[body.email] = user

        access_token = _create_access_token(user_id, body.email)
        raw_refresh = _create_refresh_token()
        token_hash = _sha256(raw_refresh)
        expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        _refresh_tokens[token_hash] = {
            "id": token_hash[:16],
            "user_id": user_id,
            "token_hash": token_hash,
            "expires_at": expires_at,
            "revoked_at": None,
            "remember_me": False,
            "created_at": now,
        }

        _set_refresh_cookie(response, raw_refresh, remember_me=False)

        return RegisterResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user_id,
                "full_name": body.full_name,
                "email": body.email,
            },
        )

    # ------------------------------------------------------------------
    # login
    # ------------------------------------------------------------------
    async def login(
        self, body: LoginRequest, response: Response
    ) -> LoginResponse:
        invalid_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                    "details": {},
                }
            },
        )

        user = _users.get(body.email)
        if user is None:
            raise invalid_exc

        if not _verify_password(body.password, user["password_hash"]):
            raise invalid_exc

        if not user["is_active"]:
            raise invalid_exc

        remember_me: bool = getattr(body, "remember_me", False) or False
        now = datetime.now(timezone.utc)
        access_token = _create_access_token(user["id"], user["email"])
        raw_refresh = _create_refresh_token()
        token_hash = _sha256(raw_refresh)
        expire_days = (
            REFRESH_TOKEN_REMEMBER_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
        )
        expires_at = now + timedelta(days=expire_days)
        _refresh_tokens[token_hash] = {
            "id": token_hash[:16],
            "user_id": user["id"],
            "token_hash": token_hash,
            "expires_at": expires_at,
            "revoked_at": None,
            "remember_me": remember_me,
            "created_at": now,
        }

        _set_refresh_cookie(response, raw_refresh, remember_me=remember_me)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user["id"],
                "full_name": user["full_name"],
                "email": user["email"],
            },
        )

    # ------------------------------------------------------------------
    # refresh  (FR-08)
    # ------------------------------------------------------------------
    async def refresh(
        self, refresh_token: str, response: Response
    ) -> RefreshResponse:
        token_hash = _sha256(refresh_token)
        record = _refresh_tokens.get(token_hash)

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_REFRESH_TOKEN",
                        "message": "Refresh token is invalid or has already been used.",
                        "details": {},
                    }
                },
            )

        if record["revoked_at"] is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "REFRESH_TOKEN_REVOKED",
                        "message": "Refresh token has been revoked.",
                        "details": {},
                    }
                },
            )

        now = datetime.now(timezone.utc)
        if record["expires_at"] < now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "REFRESH_TOKEN_EXPIRED",
                        "message": "Refresh token has expired. Please log in again.",
                        "details": {},
                    }
                },
            )

        # Revoke old token (rotation)
        record["revoked_at"] = now

        # Look up user
        user = next(
            (u for u in _users.values() if u["id"] == record["user_id"]), None
        )
        if user is None or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "USER_NOT_FOUND",
                        "message": "Associated user account could not be found.",
                        "details": {},
                    }
                },
            )

        # Issue new access token
        new_access_token = _create_access_token(user["id"], user["email"])

        # Issue new refresh token (rotate)
        new_raw_refresh = _create_refresh_token()
        new_token_hash = _sha256(new_raw_refresh)
        remember_me: bool = record.get("remember_me", False)
        expire_days = (
            REFRESH_TOKEN_REMEMBER_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
        )
        new_expires_at = now + timedelta(days=expire_days)
        _refresh_tokens[new_token_hash] = {
            "id": new_token_hash[:16],
            "user_id": user["id"],
            "token_hash": new_token_hash,
            "expires_at": new_expires_at,
            "revoked_at": None,
            "remember_me": remember_me,
            "created_at": now,
        }

        _set_refresh_cookie(response, new_raw_refresh, remember_me=remember_me)

        return RefreshResponse(
            access_token=new_access_token,
            token_type="bearer",
        )

    # ------------------------------------------------------------------
    # forgot_password
    # ------------------------------------------------------------------
    async def forgot_password(
        self, body: ForgotPasswordRequest
    ) -> ForgotPasswordResponse:
        # Enumeration-resistant: always return the same response
        user = _users.get(body.email)
        if user is not None and user["is_active"]:
            raw_token = _create_refresh_token()  # reuse entropy helper
            token_hash = _sha256(raw_token)
            now = datetime.now(timezone.utc)
            _password_resets[token_hash] = {
                "id": token_hash[:16],
                "user_id": user["id"],
                "token_hash": token_hash,
                "expires_at": now + timedelta(hours=1),
                "used_at": None,
                "created_at": now,
            }
            # In production: send email with raw_token link here.

        return ForgotPasswordResponse(
            message=(
                "If an account with that email exists, "
                "we have sent a password reset link."
            )
        )

    # ------------------------------------------------------------------
    # reset_password
    # ------------------------------------------------------------------
    async def reset_password(
        self, body: ResetPasswordRequest
    ) -> ResetPasswordResponse:
        token_hash = _sha256(body.token)
        record = _password_resets.get(token_hash)

        invalid_exc = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_RESET_TOKEN",
                    "message": "Password reset token is invalid or has expired.",
                    "details": {},
                }
            },
        )

        if record is None:
            raise invalid_exc

        now = datetime.now(timezone.utc)
        if record["expires_at"] < now:
            raise invalid_exc

        if record["used_at"] is not None:
            raise invalid_exc

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

        user = next(
            (u for u in _users.values() if u["id"] == record["user_id"]), None
        )
        if user is None:
            raise invalid_exc

        user["password_hash"] = _hash_password(body.password)
        user["updated_at"] = now
        record["used_at"] = now

        # Revoke all existing refresh tokens for this user
        for rt in _refresh_tokens.values():
            if rt["user_id"] == user["id"] and rt["revoked_at"] is None:
                rt["revoked_at"] = now

        return ResetPasswordResponse(
            message="Your password has been reset successfully."
        )

    # ------------------------------------------------------------------
    # me
    # ------------------------------------------------------------------
    async def me(self, request: Request) -> MeResponse:
        auth_header: str | None = request.headers.get("Authorization")
        if auth_header is None or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "MISSING_ACCESS_TOKEN",
                        "message": "Access token is missing.",
                        "details": {},
                    }
                },
            )

        raw_token = auth_header.split(" ", 1)[1]
        payload = _decode_access_token(raw_token)
        email: str = payload.get("email", "")
        user = _users.get(email)

        if user is None or not user["is_active"]:
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
            user={
                "id": user["id"],
                "full_name": user["full_name"],
                "email": user["email"],
            }
        )

    # ------------------------------------------------------------------
    # logout
    # ------------------------------------------------------------------
    async def logout(
        self, refresh_token: str | None, response: Response
    ) -> LogoutResponse:
        if refresh_token is not None:
            token_hash = _sha256(refresh_token)
            record = _refresh_tokens.get(token_hash)
            if record is not None and record["revoked_at"] is None:
                record["revoked_at"] = datetime.now(timezone.utc)

        _clear_refresh_cookie(response)

        return LogoutResponse(message="You have been logged out successfully.")
