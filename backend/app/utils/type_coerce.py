from typing import get_origin
from uuid import UUID


def coerce_value(expected_type, value: str):
    try:
        # Optional[...] unwrap (if needed later)
        origin = get_origin(expected_type)
        if origin is not None:
            expected_type = expected_type.__args__[0]

        if expected_type is str:
            return value

        if expected_type is int:
            return int(value)

        if expected_type is float:
            return float(value)

        if expected_type is bool:
            return value.lower() in ("true", "1", "yes", "y")

        if expected_type is UUID:
            return UUID(value)

        # fallback: unknown type → reject safely
        return None

    except Exception:
        return None