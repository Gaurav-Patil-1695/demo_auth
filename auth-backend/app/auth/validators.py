from __future__ import annotations

import re
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Password policy constants (mirrors capabilities.yaml)
# ---------------------------------------------------------------------------

PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBER = True
PASSWORD_REQUIRE_SPECIAL = False  # require_special_character=false


# ---------------------------------------------------------------------------
# Individual rule checkers
# ---------------------------------------------------------------------------

def _has_min_length(password: str) -> bool:
    return len(password) >= PASSWORD_MIN_LENGTH


def _has_uppercase(password: str) -> bool:
    return bool(re.search(r"[A-Z]", password))


def _has_lowercase(password: str) -> bool:
    return bool(re.search(r"[a-z]", password))


def _has_number(password: str) -> bool:
    return bool(re.search(r"[0-9]", password))


# ---------------------------------------------------------------------------
# Password policy validator
# Validation messages are copied VERBATIM from validation-rules.md.
# Rules are checked in the order defined there; all failures are collected.
# ---------------------------------------------------------------------------

def validate_password(password: str) -> list[str]:
    """Return a list of validation error messages for *password*.

    An empty list means the password is valid.
    Messages are emitted in the canonical order from validation-rules.md.
    """
    errors: list[str] = []

    if not _has_min_length(password):
        errors.append("Password must be at least 8 characters.")

    if PASSWORD_REQUIRE_UPPERCASE and not _has_uppercase(password):
        errors.append("Password must contain at least one uppercase letter.")

    if PASSWORD_REQUIRE_LOWERCASE and not _has_lowercase(password):
        errors.append("Password must contain at least one lowercase letter.")

    if PASSWORD_REQUIRE_NUMBER and not _has_number(password):
        errors.append("Password must contain at least one number.")

    return errors


# ---------------------------------------------------------------------------
# Field validators (used by Pydantic schemas via @validator / @field_validator)
# All messages are copied VERBATIM from validation-rules.md.
# ---------------------------------------------------------------------------

def validate_full_name(value: str) -> str:
    """Validate the full_name field.

    Raises ValueError with the exact message from validation-rules.md.
    """
    value = value.strip()
    if not value:
        raise ValueError("Full name is required.")
    if len(value) < 2:
        raise ValueError("Full name must be at least 2 characters.")
    if len(value) > 100:
        raise ValueError("Full name must be at most 100 characters.")
    return value


def validate_email_field(value: str) -> str:
    """Validate the email field.

    Raises ValueError with the exact message from validation-rules.md.
    """
    value = value.strip().lower()
    if not value:
        raise ValueError("Email is required.")
    # Basic RFC-ish pattern — the server is authoritative.
    pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
    if not re.match(pattern, value):
        raise ValueError("Please enter a valid email address.")
    return value


def validate_password_field(value: str) -> str:
    """Validate the password field via the password policy.

    Raises ValueError with the first failing message (Pydantic surfaces one at a
    time via field validators; all failures are available via validate_password).
    """
    if not value:
        raise ValueError("Password is required.")
    errors = validate_password(value)
    if errors:
        raise ValueError(errors[0])
    return value


def validate_confirm_password(password: str, confirm_password: str) -> str:
    """Cross-field validator for confirm_password.

    Raises ValueError with the exact message from validation-rules.md.
    """
    if not confirm_password:
        raise ValueError("Please confirm your password.")
    if password != confirm_password:
        raise ValueError("Passwords do not match.")
    return confirm_password


def validate_token_field(value: str, field_label: str = "Token") -> str:
    """Validate that a token field is present and non-empty."""
    value = value.strip()
    if not value:
        raise ValueError(f"{field_label} is required.")
    return value


# ---------------------------------------------------------------------------
# Password strength scoring (used by the frontend-mirrored strength meter logic
# on the backend for documentation / parity; 0-4 scale, one point per rule).
# ---------------------------------------------------------------------------

def password_strength_score(password: str) -> int:
    """Return a strength score 0-4 based on the four active policy rules.

    +1 for each passing rule: length >= 8, uppercase, lowercase, number.
    Special character is NOT counted (require_special_character=false).
    """
    score = 0
    if _has_min_length(password):
        score += 1
    if _has_uppercase(password):
        score += 1
    if _has_lowercase(password):
        score += 1
    if _has_number(password):
        score += 1
    return score
