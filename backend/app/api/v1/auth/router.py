from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from app.api.dependencies import Provider
from app.models.auth.AuthModels import (
    AuthStatusResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.services.auth.AuthService import AuthService


class AuthRouter:
    """Mounts /auth/login, /auth/refresh, and /auth/me endpoints."""

    def __init__(self) -> None:
        self._router = APIRouter(prefix="/auth", tags=["auth"])

        @self._router.post("/login", response_model=TokenResponse)
        async def login(
            body: LoginRequest,
            service: AuthService = Depends(Provider.authService),
        ) -> TokenResponse:
            return service.login(body)

        @self._router.post("/refresh", response_model=TokenResponse)
        async def refresh(
            body: RefreshRequest,
            service: AuthService = Depends(Provider.authService),
        ) -> TokenResponse:
            return service.refresh(body)

        @self._router.get("/me", response_model=AuthStatusResponse)
        async def me(
            authorization: str | None = Header(default=None),
            service: AuthService = Depends(Provider.authService),
        ) -> AuthStatusResponse:
            return service.status(authorization)

    @property
    def router(self) -> APIRouter:
        return self._router
