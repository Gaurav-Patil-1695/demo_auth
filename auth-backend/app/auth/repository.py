from __future__ import annotations

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

async def get_user_by_id(
    conn: AsyncConnection,
    user_id: int,
) -> dict | None:
    result = await conn.execute(
        text(
            "SELECT id, full_name, email, password_hash, is_active, "
            "created_at, updated_at FROM users WHERE id = :id"
        ),
        {"id": user_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_user_by_email(
    conn: AsyncConnection,
    email: str,
) -> dict | None:
    result = await conn.execute(
        text(
            "SELECT id, full_name, email, password_hash, is_active, created_at, updated_at "
            "FROM users WHERE email = :email"
        ),
        {"email": email},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def create_user(
    conn: AsyncConnection,
    full_name: str,
    email: str,
    password_hash: str,
) -> dict:
    result = await conn.execute(
        text(
            "INSERT INTO users (full_name, email, password_hash, is_active) "
            "VALUES (:full_name, :email, :password_hash, TRUE) "
            "RETURNING id, full_name, email, password_hash, "
            "is_active, created_at, updated_at"
        ),
        {"full_name": full_name, "email": email, "password_hash": password_hash},
    )
    row = result.mappings().first()
    return dict(row)  # type: ignore[arg-type]


async def update_user_password(
    conn: AsyncConnection,
    user_id: int,
    password_hash: str,
) -> None:
    await conn.execute(
        text(
            "UPDATE users SET password_hash = :password_hash, updated_at = NOW() "
            "WHERE id = :id"
        ),
        {"password_hash": password_hash, "id": user_id},
    )


# ---------------------------------------------------------------------------
# Password resets
# ---------------------------------------------------------------------------

async def create_password_reset(
    conn: AsyncConnection,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
) -> dict:
    result = await conn.execute(
        text(
            "INSERT INTO password_resets (user_id, token_hash, expires_at) "
            "VALUES (:user_id, :token_hash, :expires_at) "
            "RETURNING id, user_id, token_hash, expires_at, used_at, created_at"
        ),
        {"user_id": user_id, "token_hash": token_hash, "expires_at": expires_at},
    )
    row = result.mappings().first()
    return dict(row)  # type: ignore[arg-type]


async def get_password_reset_by_token_hash(
    conn: AsyncConnection,
    token_hash: str,
) -> dict | None:
    result = await conn.execute(
        text(
            "SELECT id, user_id, token_hash, expires_at, used_at, created_at "
            "FROM password_resets "
            "WHERE token_hash = :token_hash"
        ),
        {"token_hash": token_hash},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def mark_password_reset_used(
    conn: AsyncConnection,
    reset_id: int,
) -> None:
    await conn.execute(
        text(
            "UPDATE password_resets SET used_at = NOW() WHERE id = :id"
        ),
        {"id": reset_id},
    )


async def invalidate_previous_password_resets(
    conn: AsyncConnection,
    user_id: int,
) -> None:
    """Mark all unused, unexpired resets for a user as used before issuing a new one."""
    await conn.execute(
        text(
            "UPDATE password_resets "
            "SET used_at = NOW() "
            "WHERE user_id = :user_id AND used_at IS NULL AND expires_at > NOW()"
        ),
        {"user_id": user_id},
    )


# ---------------------------------------------------------------------------
# Refresh tokens
# ---------------------------------------------------------------------------

async def create_refresh_token(
    conn: AsyncConnection,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
    remember_me: bool,
) -> dict:
    result = await conn.execute(
        text(
            "INSERT INTO refresh_tokens (user_id, token_hash, expires_at, remember_me) "
            "VALUES (:user_id, :token_hash, :expires_at, :remember_me) "
            "RETURNING id, user_id, token_hash, expires_at, "
            "revoked_at, remember_me, created_at"
        ),
        {
            "user_id": user_id,
            "token_hash": token_hash,
            "expires_at": expires_at,
            "remember_me": remember_me,
        },
    )
    row = result.mappings().first()
    return dict(row)  # type: ignore[arg-type]


async def get_refresh_token_by_token_hash(
    conn: AsyncConnection,
    token_hash: str,
) -> dict | None:
    result = await conn.execute(
        text(
            "SELECT id, user_id, token_hash, expires_at, revoked_at, "
            "remember_me, created_at "
            "FROM refresh_tokens "
            "WHERE token_hash = :token_hash"
        ),
        {"token_hash": token_hash},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def revoke_refresh_token(
    conn: AsyncConnection,
    token_id: int,
) -> None:
    await conn.execute(
        text(
            "UPDATE refresh_tokens SET revoked_at = NOW() WHERE id = :id"
        ),
        {"id": token_id},
    )


async def revoke_all_refresh_tokens_for_user(
    conn: AsyncConnection,
    user_id: int,
) -> None:
    await conn.execute(
        text(
            "UPDATE refresh_tokens "
            "SET revoked_at = NOW() "
            "WHERE user_id = :user_id AND revoked_at IS NULL"
        ),
        {"user_id": user_id},
    )


async def rotate_refresh_token(
    conn: AsyncConnection,
    old_token_id: int,
    user_id: int,
    new_token_hash: str,
    expires_at: datetime,
    remember_me: bool,
) -> dict:
    """Revoke the old refresh token and issue a new one atomically."""
    await revoke_refresh_token(conn, old_token_id)
    return await create_refresh_token(
        conn,
        user_id=user_id,
        token_hash=new_token_hash,
        expires_at=expires_at,
        remember_me=remember_me,
    )
