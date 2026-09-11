from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Shared / envelope
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ---------------------------------------------------------------------------
# /auth/login
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address.")
    password: str = Field(..., description="User password.")
    remember_me: Optional[bool] = Field(None, description="Extend refresh token lifetime.")


class MeResponse(BaseModel):
    id: str
    full_name: str
    email: str
    is_active: bool
    created_at: datetime


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: MeResponse


# ---------------------------------------------------------------------------
# /auth/register
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    full_name: str = Field(..., description="User full name.")
    email: EmailStr = Field(..., description="User email address.")
    password: str = Field(..., description="User password.")
    confirm_password: str = Field(..., description="Password confirmation.")


class RegisterResponse(BaseModel):
    access_token: str
    token_type: str
    user: MeResponse


# ---------------------------------------------------------------------------
# /auth/forgot-password
# ---------------------------------------------------------------------------


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to send the reset link to.")


class ForgotPasswordResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# /auth/reset-password
# ---------------------------------------------------------------------------


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token received via email.")
    password: str = Field(..., description="New password.")
    confirm_password: str = Field(..., description="New password confirmation.")


class ResetPasswordResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# /auth/logout
# ---------------------------------------------------------------------------


class LogoutResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# /auth/refresh
# ---------------------------------------------------------------------------


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str
