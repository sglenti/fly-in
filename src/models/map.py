from typing import Dict, List, Optional, Set, Tuple
from models import Zone, Connection, ZoneType
import json


class Map():
    def __init__(self) -> None:
        self._zones: Dict[str, Zone] = {}
        self._connections: List[Connection] = []
        self._adj_list: Dict[str, List[Connection]] = {}
        self._start_zone: Optional[Zone] = None
        self._end_zone: Optional[Zone] = None

    def get_zones(self) -> Dict[str, Zone]:
        return self._zones

    def get_conn_list(self) -> List[Connection]:
        return self._connections

    def get_adj_list(self) -> Dict[str, List[Connection]]:
        return self._adj_list

    def get_end(self) -> str:
        if self._end_zone is None:
            raise RuntimeError("Map has no end zone")
        end_zone: str = self._end_zone.name
        return end_zone

    def get_start(self) -> str:
        if self._start_zone is None:
            raise RuntimeError("Map has no end zone")
        start_zone: str = self._start_zone.name
        return start_zone

    def set_start_zone(self, zone: Zone) -> None:
        if self._start_zone is not None:
            raise ValueError(
                    f"Map already has a start zone: {self._start_zone.name}")
        self._start_zone = zone

    def is_restricted(self, zone: str) -> bool:
        return self._zones[zone].metadata.zone_type == ZoneType.RESTRICTED

    def get_connection(
            self,
            node1: str | None,
            node2: str | None
            ) -> Optional[Connection]:
        if node1 and node2 and node1 != node2:
            for conn in self._adj_list.get(node1, []):
                if conn.end_point1 == node2 or conn.end_point2 == node2:
                    return conn
        return None

    def set_end_zone(self, zone: Zone) -> None:
        if self._end_zone is not None:
            raise ValueError(
                    f"Map already has an end zone: {self._end_zone.name}")
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
        processed_pairs: Set[Tuple[str, str]] = set()

        for conn in self._connections:
            if (conn.end_point1 not in self._zones
                    or conn.end_point2 not in self._zones):
                raise ValueError(
                    "Invalid hub name in connection "
                    f"{conn.end_point1}-{conn.end_point2}")
            if conn.end_point1 == conn.end_point2:
                raise ValueError(
                    "Connection source and target must differ: "
                    f"{conn.end_point1}-{conn.end_point2}")

            pair = tuple(sorted((conn.end_point1, conn.end_point2)))
            if pair in processed_pairs:
                raise ValueError("Duplicated connection: "
                                 f"{conn.end_point1}-{conn.end_point2}")

            if conn.end_point1 not in self._adj_list:
                self._adj_list[conn.end_point1] = []
            self._adj_list[conn.end_point1].append(conn)
            if conn.end_point2 not in self._adj_list:
                self._adj_list[conn.end_point2] = []
            self._adj_list[conn.end_point2].append(conn)

    def to_json(self) -> str:
        data = {
            "zones": {name: z.model_dump() for name, z in self._zones.items()},
            "connections": [c.model_dump() for c in self._connections]
        }
        return json.dumps(data, indent=4)

    def print_topology(self) -> None:
        for zone_name, connections in self._adj_list.items():
            targets = [c.end_point2 if c.end_point1 == zone_name
                       else c.end_point1 for c in connections]
            print(f"<{zone_name}>: {' | '.join(targets)}")

    @property
    def start_zone_name(self) -> str:
        return self.get_start()
