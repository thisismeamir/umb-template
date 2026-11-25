from __future__ import annotations

from fastapi import HTTPException, status

from app.config import Settings, get_settings
from app.engine.auth.TokenEngine import TokenEngine, TokenError
from app.models.auth.AuthModels import (
    AuthStatusResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserPrincipal,
)


class AuthService:
    """Handles JWT login, token refresh, and toggleable bearer authentication."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._tokens = TokenEngine(self._settings.authSecretKey)

    def _rolesFor(self, username: str) -> list[str]:
        if username in self._settings.authAdminUsers:
            return ["reader", "writer", "admin"]
        return ["reader", "writer"]

    def _mintPair(self, username: str, roles: list[str]) -> TokenResponse:
        access_ttl = self._settings.authAccessTokenMinutes * 60
        refresh_ttl = self._settings.authRefreshTokenDays * 86400
        return TokenResponse(
            accessToken=self._tokens.encode(
                subject=username,
                roles=roles,
                token_type="access",
                ttl_seconds=access_ttl,
            ),
            refreshToken=self._tokens.encode(
                subject=username,
                roles=roles,
                token_type="refresh",
                ttl_seconds=refresh_ttl,
            ),
            expiresIn=access_ttl,
        )

    def login(self, request: LoginRequest) -> TokenResponse:
        roles = self._rolesFor(request.username)
        return self._mintPair(request.username, roles)

    def refresh(self, request: RefreshRequest) -> TokenResponse:
        try:
            payload = self._tokens.decode(
                request.refreshToken, expected_type="refresh"
            )
        except TokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            )
        username = str(payload["sub"])
        roles = list(payload.get("roles") or self._rolesFor(username))
        return self._mintPair(username, roles)

    def resolvePrincipal(self, authorization: str | None) -> UserPrincipal:
        """Resolve current user from Authorization header; allow anonymous when auth is disabled."""
        if authorization and authorization.lower().startswith("bearer "):
            raw_token = authorization.split(" ", 1)[1].strip()
            try:
                payload = self._tokens.decode(raw_token, expected_type="access")
                return UserPrincipal(
                    username=str(payload["sub"]),
                    roles=list(payload.get("roles") or ["reader"]),
                    authenticated=True,
                )
            except TokenError as exc:
                if self._settings.authEnabled:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=str(exc),
                        headers={"WWW-Authenticate": "Bearer"},
                    )

        if self._settings.authEnabled:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return UserPrincipal(
            username="anonymous",
            roles=["reader", "writer"],
            authenticated=False,
        )

    def status(self, authorization: str | None) -> AuthStatusResponse:
        principal = self.resolvePrincipal(authorization)
        return AuthStatusResponse(
            authEnabled=self._settings.authEnabled,
            authenticated=principal.authenticated,
            user=principal,
        )
