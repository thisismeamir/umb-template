from enum import Enum

from pydantic import BaseModel

class EntryFieldType(str, Enum):
    NAME = "name"
    IDENTIFIER = "identifier"
    VERSION = "version"
    TYPE = "type"
    SOURCE = "source"        # which system wrote it
    ENTRY_TYPE = "entry_type"
    CREATED_BY = "created_by"
    METADATA = "metadata"    # targets JSONB keys

class EntryFieldModel(BaseModel):
    key: str
    value: str
    isColumn: bool = False