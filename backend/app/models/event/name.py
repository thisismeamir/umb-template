from typing import List

from pydantic import BaseModel


class EventName(BaseModel):
    # from generator prefix
    generator: str | None = None
    # full process string e.g. "gammae_eZ_Zqq"
    process_raw: str | None
    # ecm extracted from the suffix
    ecm_gev: float | None  # 365.0