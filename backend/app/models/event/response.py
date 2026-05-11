from typing import List, Optional
from app.config import Settings
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

class Event(BaseModel):

    entity_id: int
    uuid: UUID
    name: str

    created_at: datetime
    updated_at: datetime
    last_edited_at: Optional[datetime] = None

    # ---------------------------------------------------------------------
    # FK-resolved fields (keep both id + name → avoids joins later)
    # ---------------------------------------------------------------------
    accelerator_id: int
    accelerator_name: str

    stage_id: int
    stage_name: str

    campaign_id: int
    campaign_name: str

    detector_id: int
    detector_name: str

    file_type_id: int
    file_type_name: str

    # ---------------------------------------------------------------------
    # File / dataset metadata
    # ---------------------------------------------------------------------
    path: str
    size: int
    status: str
    comment: Optional[str] = None
    description: Optional[str] = None

    # ---------------------------------------------------------------------
    # Physics / generator metadata
    # (normalize names but preserve original JSON via alias)
    # ---------------------------------------------------------------------
    gen_type: Optional[str] = Field(None, alias="gen-type")
    rec_type: Optional[str] = Field(None, alias="rec-type")
    sim_type: Optional[str] = Field(None, alias="sim-type")

    k_factor: Optional[float] = Field(None, alias="k-factor")
    matching_eff: Optional[float] = Field(None, alias="matching-eff")

    cross_section: Optional[float] = Field(None, alias="cross-section")
    sum_of_weights: Optional[float] = Field(None, alias="sum-of-weights")

    n_events: Optional[int] = Field(None, alias="n-events")

    # ---------------------------------------------------------------------
    # File quality
    # ---------------------------------------------------------------------
    n_files_good: Optional[int] = Field(None, alias="n-files-good")
    n_files_bad: Optional[int] = Field(None, alias="n-files-bad")
    n_files_eos: Optional[int] = Field(None, alias="n-files-eos")

    # ---------------------------------------------------------------------
    # Environment
    # ---------------------------------------------------------------------
    key4hep_stack: Optional[str] = Field(None, alias="key4hep-stack")
    produced_with: Optional[str] = Field(None, alias="produced-with")

class EventListResponse(BaseModel):
    results: List[Event]

    total: Optional[int] = None
    limit: int
    offset: int
    
class BulkEventListResponse(BaseModel):
    results: List[EventListResponse]