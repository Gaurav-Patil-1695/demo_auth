from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
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
    LogoutResponse,
    RefreshResponse,
    ErrorResponse,
)
from app.auth import service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    operation_id="login",
    responses={
        401: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
    },
)
async def login(
    body: LoginRequest,
    response: Response,
    request: Request,
) -> LoginResponse:
    return await service.login(body=body, response=response, request=request)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="register",
    responses={
        409: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def register(
    body: RegisterRequest,
    response: Response,
    request: Request,
) -> RegisterResponse:
    return await service.register(body=body, response=response, request=request)


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="forgotPassword",
    responses={
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
    },
)
async def forgotPassword(
    body: ForgotPasswordRequest,
    request: Request,
) -> ForgotPasswordResponse:
    return await service.forgotPassword(body=body, request=request)


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
    operation_id="resetPassword",
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def resetPassword(
    body: ResetPasswordRequest,
) -> ResetPasswordResponse:
    return await service.resetPassword(body=body)


@router.get(
    "/me",
    response_model=MeResponse,
    status_code=status.HTTP_200_OK,
    operation_id="me",
    responses={
        401: {"model": ErrorResponse},
    },
)
async def me(
    request: Request,
) -> MeResponse:
    return await service.me(request=request)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    operation_id="logout",
    responses={
        401: {"model": ErrorResponse},
    },
)
async def logout(
    request: Request,
    response: Response,
) -> LogoutResponse:
    return await service.logout(request=request, response=response)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
    operation_id="refresh",
    responses={
        401: {"model": ErrorResponse},
    },
)
async def refresh(
    request: Request,
    response: Response,
) -> RefreshResponse:
    return await service.refresh(request=request, response=response)
