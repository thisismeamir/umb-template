from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any


class TokenError(ValueError):
    """Raised when a JWT token is malformed, invalid, or expired."""


def _b64urlEncode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64urlDecode(segment: str) -> bytes:
    padding = "=" * ((4 - len(segment) % 4) % 4)
    return base64.urlsafe_b64decode(segment + padding)


class TokenEngine:
    """Stateless RFC 7519 HS256 JWT encoder/decoder using Python stdlib cryptography."""

    HEADER_B64 = _b64urlEncode(
        json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode("utf-8")
    )

    def __init__(self, secret_key: str) -> None:
        self._secret = secret_key.encode("utf-8")

    def encode(
        self,
        *,
        subject: str,
        roles: list[str],
        token_type: str,
        ttl_seconds: int,
    ) -> str:
        now = int(time.time())
        payload = {
            "sub": subject,
            "roles": roles,
            "type": token_type,
            "iat": now,
            "exp": now + ttl_seconds,
        }
        payload_b64 = _b64urlEncode(
            json.dumps(payload, separators=(",", ":")).encode("utf-8")
        )
        signing_input = f"{self.HEADER_B64}.{payload_b64}".encode("ascii")
        sig = hmac.new(self._secret, signing_input, hashlib.sha256).digest()
        return f"{self.HEADER_B64}.{payload_b64}.{_b64urlEncode(sig)}"

    def decode(
        self, token: str, *, expected_type: str | None = None
    ) -> dict[str, Any]:
        parts = token.split(".")
        if len(parts) != 3:
            raise TokenError("Malformed JWT structure")

        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = _b64urlEncode(
            hmac.new(self._secret, signing_input, hashlib.sha256).digest()
        )
        if not hmac.compare_digest(sig_b64, expected_sig):
            raise TokenError("Invalid token signature")

        try:
            payload: dict[str, Any] = json.loads(_b64urlDecode(payload_b64).decode("utf-8"))
        except Exception as exc:
            raise TokenError("Invalid token payload") from exc

        exp = payload.get("exp")
        if not isinstance(exp, int) or exp < int(time.time()):
            raise TokenError("Token has expired")

        if expected_type is not None and payload.get("type") != expected_type:
            raise TokenError(f"Expected '{expected_type}' token")

        return payload
