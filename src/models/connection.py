"""Data model definitions for graph elements in the simulation."""

from pydantic import BaseModel, Field


class Connection(BaseModel):
    """Represents a directed or undirected link between two zones.

    Attributes:
        end_point1: First endpoint of the connection.
        end_point2: Second endpoint of the connection.
        max_link_capacity: Maximum number of drones allowed on the link at once.
    """

    end_point1: str
    end_point2: str
    max_link_capacity: int = Field(default=1, gt=0)
    model_config = {
        'extra': 'forbid',
        'frozen': True
    }
