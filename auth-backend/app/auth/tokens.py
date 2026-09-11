from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import jwt

from app.config.settings import settings

# ---------------------------------------------------------------------------
# TTL constants
# ---------------------------------------------------------------------------

ACCESS_TOKEN_TTL_MINUTES: int = 15

# Refresh token TTL variants
REFRESH_TOKEN_TTL_DAYS: int = 1          # standard session
REFRESH_TOKEN_TTL_REMEMBER_ME_DAYS: int = 30  # extended when rememberMe=True

# Password-reset token TTL
PASSWORD_RESET_TOKEN_TTL_MINUTES: int = 60

# ---------------------------------------------------------------------------
# Hashing helpers
# ---------------------------------------------------------------------------


def hash_token(raw_token: str) -> str:
    """Return the SHA-256 hex digest of *raw_token*.

    Tokens are stored only in hashed form (NFR-02, NFR-04).
    Comparison is always performed by hashing the incoming value and comparing
    against the stored hash — the raw token is never persisted.
    """
    return hashlib.sha256(raw_token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Opaque token generation  (refresh + password-reset)
# ---------------------------------------------------------------------------


def generate_opaque_token() -> str:
    """Return a URL-safe, cryptographically random opaque token string."""
    return secrets.token_urlsafe(32)


# ---------------------------------------------------------------------------
# Access token (JWT)
# ---------------------------------------------------------------------------


def create_access_token(
    user_id: int,
    extra_claims: Optional[dict[str, Any]] = None,
) -> str:
    """Create a signed JWT access token for *user_id*.

    The token expires in ACCESS_TOKEN_TTL_MINUTES minutes from now (UTC).
    Additional claims can be injected via *extra_claims*.
    """
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_TTL_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify *token*; raise ``jose.JWTError`` on any failure."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )


# ---------------------------------------------------------------------------
# Refresh token
# ---------------------------------------------------------------------------


def create_refresh_token(remember_me: bool = False) -> tuple[str, str, datetime]:
    """Generate a new opaque refresh token.

    Returns a tuple of ``(raw_token, token_hash, expires_at)``.

    When *remember_me* is ``True`` the TTL is extended to
    REFRESH_TOKEN_TTL_REMEMBER_ME_DAYS; otherwise REFRESH_TOKEN_TTL_DAYS is used.
    The ``expires_at`` timestamp is UTC-aware.
    """
    ttl_days = (
        REFRESH_TOKEN_TTL_REMEMBER_ME_DAYS if remember_me else REFRESH_TOKEN_TTL_DAYS
    )
    raw_token = generate_opaque_token()
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(tz=timezone.utc) + timedelta(days=ttl_days)
    return raw_token, token_hash, expires_at


def is_refresh_token_valid(token_record: dict[str, Any]) -> bool:
    """Return True when *token_record* is neither revoked nor expired."""
    if token_record.get("revoked_at") is not None:
        return False

    expires_at: datetime = token_record["expires_at"]
    # Ensure comparison is timezone-aware
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return datetime.now(tz=timezone.utc) < expires_at


# ---------------------------------------------------------------------------
# Refresh token rotation
# ---------------------------------------------------------------------------


def create_rotated_refresh_token(
    remember_me: bool = False,
) -> tuple[str, str, datetime]:
    """Produce a replacement refresh token during rotation.

    Rotation means: the caller revokes the old DB row, then persists a new one
    using the values returned here.  The ``remember_me`` flag is preserved from
    the original token so the TTL class is retained across rotations.

    Returns ``(raw_token, token_hash, expires_at)`` identical to
    :func:`create_refresh_token`.
    """
    return create_refresh_token(remember_me=remember_me)


# ---------------------------------------------------------------------------
# Password-reset token
# ---------------------------------------------------------------------------


def create_password_reset_token() -> tuple[str, str, datetime]:
    """Generate a short-lived opaque password-reset token.

    Returns ``(raw_token, token_hash, expires_at)``.

    The raw token is sent to the user via email; only the hash is stored in the
    ``password_resets`` table (NFR-04).  The token expires in
    PASSWORD_RESET_TOKEN_TTL_MINUTES minutes from now (UTC).
    """
    raw_token = generate_opaque_token()
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(tz=timezone.utc) + timedelta(
        minutes=PASSWORD_RESET_TOKEN_TTL_MINUTES
    )
    return raw_token, token_hash, expires_at


def is_password_reset_token_valid(token_record: dict[str, Any]) -> bool:
    """Return True when *token_record* is unused and not yet expired."""
    if token_record.get("used_at") is not None:
        return False

    expires_at: datetime = token_record["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return datetime.now(tz=timezone.utc) < expires_at
