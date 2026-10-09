"""Drone-related data models used by the simulation."""

from typing import List, Tuple
from pydantic import BaseModel, Field
from enum import Enum


class DroneStatus(str, Enum):
    """Lifecycle state for a drone during the simulation.

    Values describe whether a drone is waiting, moving, in transit between
    zones, or has completed its route.
    """

    WAITING = "waiting"
    MOVING = "moving"
    IN_TRANSIT = "in_transit"  # For 2-turn movements
    DELIVERED = "delivered"


class Drone(BaseModel):
    """Represents a drone in the simulation.

    Attributes:
        id: Unique identifier for the drone.
        current_location: Current zone name, or ``None`` while traversing a link.
        status: Current operational status.
        path: Planned route as a sequence of ``(zone_name, turn)`` pairs.
    """

    id: str
    current_location: str | None
    status: DroneStatus = DroneStatus.WAITING
    path: List[Tuple[str, int]] = Field(default_factory=list)
