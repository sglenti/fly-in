from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import Optional


class ZoneType(str, Enum):
    NORMAL = "normal"
    RESTRICTED = "restricted"
    PRIORITY = "priority"
    BLOCKED = "blocked"


class ZoneMetadata(BaseModel):
    zone_type: ZoneType = ZoneType.NORMAL
    color: Optional[str] = None
    max_drones: int = Field(default=1, gt=0)
    model_config = {
        'extra': 'forbid'
    }


class Zone(BaseModel):
    name: str
    x: int
    y: int
    metadata: ZoneMetadata = Field(default_factory=ZoneMetadata)

    @field_validator('name')
    @classmethod
    def name_must_not_have_dashes(cls, v: str) -> str:
        if '-' in v:
            raise ValueError('Zone name cannot contain dashes')
        return v
