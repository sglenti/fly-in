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
        if self._start_zone == self._end_zone:
            raise ValueError("Start and End hubs must differ!") 
        # fill adj_list (if duplicates, raise error)
        processed_pairs = set()

        for conn in self._connections:
            if (conn.source_name not in self._zones
                    or conn.target_name not in self._zones):
                raise ValueError("Invalid hub name in connection "
                    f"{conn.source_name}-{conn.target_name}")
            if conn.source_name == conn.target_name:
                raise ValueError("Connection source and target must differ: "
                    f"{conn.source_name}-{conn.target_name}")

            pair = tuple(sorted((conn.source_name, conn.target_name)))
            if pair in processed_pairs:
                raise ValueError("Duplicated connection: "
                    f"{conn.source_name}-{conn.target_name}")

            if conn.source_name not in self._adj_list:
                self._adj_list[conn.source_name] = []
            self._adj_list[conn.source_name].append(conn)
            if conn.target_name not in self._adj_list:
                self._adj_list[conn.target_name] = []
            self._adj_list[conn.target_name].append(conn)

    def to_json(self) -> str:
        data = {
            "zones": {name: z.model_dump() for name, z in self._zones.items()},
            "connections": [c.model_dump() for c in self._connections]
        }
        return json.dumps(data, indent=4)

    def print_topology(self):
        for zone_name, connections in self._adj_list.items():
            targets = [c.target_name if c.source_name == zone_name 
                    else c.source_name for c in connections]
            print(f"<{zone_name}>: {' | '.join(targets)}")
