from typing import List
from pydantic import BaseModel, Field
from enum import Enum


class DroneStatus(str, Enum):
    WAITING = "waiting"
    MOVING = "moving"
    IN_TRANSIT = "in_transit"  # For 2-turn movements
    DELIVERED = "delivered"


class Drone(BaseModel):
    id: str
    current_location: str
    status: DroneStatus = DroneStatus.WAITING
    path: List[str] = Field(default_factory=list)
