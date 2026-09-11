from pydantic import BaseModel
from typing import Any, Dict, Optional


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = {}


class ErrorResponse(BaseModel):
    error: ErrorDetail


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    confirm_password: str


class RegisterResponse(BaseModel):
    id: str
    full_name: str
    email: str
    created_at: str


class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: Optional[bool] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class ForgotPasswordRequest(BaseModel):
    email: str


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    confirm_password: str


class ResetPasswordResponse(BaseModel):
    message: str


class MeResponse(BaseModel):
    id: str
    full_name: str
    email: str
    created_at: str


class LogoutResponse(BaseModel):
    message: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
