from typing import Dict, List, Optional
from models import Zone, Connection
import json


class Map():
    def __init__(self) -> None:
        self._zones: Dict[str, Zone] = {}
        self._connections: List[Connection] = []
        self._adj_list: Dict[str, List[Connection]] = {}
        self.start_zone: Optional[Zone]
        self.end_zone: Optional[Zone]

    def set_start_zone(self, zone: Zone) -> None:
        pass

    def set_end_zone(self, zone: Zone) -> None:
        pass

    def add_zone(self, zone: Zone) -> None:
        # add to registry (if duplicates, raise error)
        pass

    def add_connection(self, connection: Connection) -> None:
        # add to connections (if duplicates, raise error)
        pass

    def initialize_graph(self) -> None:
        # fill adj_list (if duplicates, raise error)
        pass

    def to_json(self) -> str:
        data = {
            "zones": {name: z.model_dump() for name, z in self._zones.items()},
            "connections": [c.model_dump() for c in self._connections]
        }
        return json.dumps(data, indent=4)
