"""Zone and metadata models for the flight map graph."""

from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import Optional


class ZoneType(str, Enum):
    """Possible behaviour classes that can be assigned to a zone."""

    NORMAL = "normal"
    RESTRICTED = "restricted"
    PRIORITY = "priority"
    BLOCKED = "blocked"


class ZoneMetadata(BaseModel):
    """Configuration metadata attached to a zone.

    Attributes:
        zone_type: Semantic type of the zone.
        color: Optional display color used by the renderer.
        max_drones: Maximum number of simultaneous drones allowed in the zone.
    """

    zone_type: ZoneType = ZoneType.NORMAL
    color: Optional[str] = None
    max_drones: int = Field(default=1, gt=0)
    model_config = {
        'extra': 'forbid'
    }


class Zone(BaseModel):
    """Represents a single hub or node in the map graph.

    Attributes:
        name: Unique zone name.
        x: Horizontal coordinate of the zone.
        y: Vertical coordinate of the zone.
        metadata: Additional zone configuration and constraints.
    """

    name: str
    x: int
    y: int
    metadata: ZoneMetadata = Field(default_factory=ZoneMetadata)

    @field_validator('name')
    @classmethod
    def name_must_not_have_dashes(cls, v: str) -> str:
        """Reject names containing dashes because they are reserved in parsing.

        Args:
            v: Proposed zone name.

        Returns:
            The validated name.

        Raises:
            ValueError: If the name contains a dash.
        """
        if '-' in v:
            raise ValueError('Zone name cannot contain dashes')
        return v
