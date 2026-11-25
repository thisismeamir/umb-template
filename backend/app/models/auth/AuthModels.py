from __future__ import annotations

from pydantic import BaseModel, Field


class UserPrincipal(BaseModel):
    username: str
    roles: list[str] = Field(default_factory=lambda: ["reader"])
    authenticated: bool = True


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class RefreshRequest(BaseModel):
    refreshToken: str = Field(min_length=1)


class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "bearer"
    expiresIn: int


class AuthStatusResponse(BaseModel):
    authEnabled: bool
    authenticated: bool
    user: UserPrincipal | None = None
