from typing import Dict, List, Optional
from models import Zone, Connection
import json


class Map():
    def __init__(self) -> None:
        self._zones: Dict[str, Zone] = {}
        self._connections: List[Connection] = []
        self._adj_list: Dict[str, List[Connection]] = {}
        self._start_zone: Optional[Zone] = None
        self._end_zone: Optional[Zone] = None

    def set_start_zone(self, zone: Zone) -> None:
        if self._start_zone is not None:
            raise ValueError(f"Map already has a start zone: {self._start_zone.name}")
        self._start_zone = zone

    def set_end_zone(self, zone: Zone) -> None:
        if self._end_zone is not None:
            raise ValueError(f"Map already has an end zone: {self._end_zone.name}")
        self._end_zone = zone

    def add_zone(self, zone: Zone) -> None:
        # add to registry (if duplicates, raise error)
        if zone.name in self._zones.keys():
            raise ValueError("Duplicated hub name")
        self._zones[zone.name] = zone

    def add_connection(self, connection: Connection) -> None:
        # add to connections
        self._connections.append(connection)

    def initialize_graph(self) -> None:
        # fill adj_list (if duplicates, raise error)
        pass

    def to_json(self) -> str:
        data = {
            "zones": {name: z.model_dump() for name, z in self._zones.items()},
            "connections": [c.model_dump() for c in self._connections]
        }
        return json.dumps(data, indent=4)
