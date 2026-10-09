"""Graph model representing the map topology used by the simulation."""

from typing import Dict, List, Optional, Set, Tuple
from src.models import Zone, Connection, ZoneType
import json


class Map:
    """Represents the simulation graph and all normalized route metadata.

    The map keeps track of zones, connections, start/end hubs, and adjacency
    relationships required for connectivity checks and pathfinding.
    """

    def __init__(self) -> None:
        """Initialize an empty map graph."""
        self._zones: Dict[str, Zone] = {}
        self._connections: List[Connection] = []
        self._adj_list: Dict[str, List[Connection]] = {}
        self._start_zone: Optional[Zone] = None
        self._end_zone: Optional[Zone] = None

    def get_zones(self) -> Dict[str, Zone]:
        """Return all registered zones in the map.

        Returns:
            Dictionary mapping zone names to their model objects.
        """
        return self._zones

    def get_conn_list(self) -> List[Connection]:
        """Return the list of all map connections.

        Returns:
            All connection objects currently registered in the map.
        """
        return self._connections

    def get_adj_list(self) -> Dict[str, List[Connection]]:
        """Return the adjacency list describing neighbor relationships.

        Returns:
            A mapping of each zone to the connections incident to it.
        """
        return self._adj_list

    def get_end(self) -> str:
        """Return the name of the end zone.

        Returns:
            The configured destination zone name.

        Raises:
            RuntimeError: If no end zone has been set.
        """
        if self._end_zone is None:
            raise RuntimeError("Map has no end zone!")
        end_zone: str = self._end_zone.name
        return end_zone

    def get_start(self) -> str:
        """Return the name of the start zone.

        Returns:
            The configured source zone name.

        Raises:
            RuntimeError: If no start zone has been set.
        """
        if self._start_zone is None:
            raise RuntimeError("Map has no start zone!")
        start_zone: str = self._start_zone.name
        return start_zone

    def set_start_zone(self, zone: Zone) -> None:
        """Set the map start zone.

        Args:
            zone: Zone to assign as the origin of the network.

        Raises:
            ValueError: If a start zone is already defined.
        """
        if self._start_zone is not None:
            raise ValueError(
                f"Cannot set '{zone.name}' as start zone"
                f"\n Map already has a start zone: '{self._start_zone.name}'")
        self._start_zone = zone

    def set_end_zone(self, zone: Zone) -> None:
        """Set the map end zone.

        Args:
            zone: Zone to assign as the destination of the network.

        Raises:
            ValueError: If an end zone is already defined.
        """
        if self._end_zone is not None:
            raise ValueError(
                f"Cannot set '{zone.name}' as end zone"
                f"\n Map already has an end zone: '{self._end_zone.name}'")
        self._end_zone = zone

    def is_restricted(self, zone: str) -> bool:
        """Check whether a zone is restricted.

        Args:
            zone: Name of the zone to inspect.

        Returns:
            ``True`` when the zone is marked restricted, otherwise ``False``.
        """
        return bool(
                self._zones[zone].metadata.zone_type == ZoneType.RESTRICTED)

    def get_connection(
            self,
            node1: str | None,
            node2: str | None
            ) -> Optional[Connection]:
        """Return the connection between two zones, if it exists.

        Args:
            node1: Name of the first zone.
            node2: Name of the second zone.

        Returns:
            The matching connection object or ``None`` if no direct connection is
            found.
        """
        if node1 and node2 and node1 != node2:
            for conn in self._adj_list.get(node1, []):
                if conn.end_point1 == node2 or conn.end_point2 == node2:
                    return conn
        return None

    def add_zone(self, zone: Zone) -> None:
        """Add a zone to the map.

        Args:
            zone: Zone instance to register.

        Raises:
            ValueError: If a zone with the same name already exists.
        """
        if zone.name in self._zones.keys():
            raise ValueError(f"Duplicated zone name: '{zone.name}'")
        self._zones[zone.name] = zone

    def add_connection(self, connection: Connection) -> None:
        """Add a connection to the map.

        Args:
            connection: Connection to register in the topology list.
        """
        self._connections.append(connection)

    def initialize_graph(self) -> None:
        """Build the adjacency structure and validate map integrity.

        Raises:
            ValueError: If the start/end zones are missing or invalid, or if a
                connection references an unknown zone.
        """
        if self._start_zone is None:
            raise ValueError("Map needs a start zone!")
        if self._end_zone is None:
            raise ValueError("Map needs an end zone!")
        if self._start_zone == self._end_zone:
            raise ValueError("Start and End hubs must differ!")

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
                                 f"'{conn.end_point1}-{conn.end_point2}'")
            processed_pairs.add((pair[0], pair[1]))

            if conn.end_point1 not in self._adj_list:
                self._adj_list[conn.end_point1] = []
            self._adj_list[conn.end_point1].append(conn)
            if conn.end_point2 not in self._adj_list:
                self._adj_list[conn.end_point2] = []
            self._adj_list[conn.end_point2].append(conn)

    def to_json(self) -> str:
        """Serialize the map to a JSON string.

        Returns:
            JSON representation of all zones and connections.
        """
        data = {
            "zones": {name: z.model_dump() for name, z in self._zones.items()},
            "connections": [c.model_dump() for c in self._connections]
        }
        return json.dumps(data, indent=4)

    def print_topology(self) -> None:
        """Print the adjacency structure for debugging purposes."""
        for zone_name, connections in self._adj_list.items():
            targets = [c.end_point2 if c.end_point1 == zone_name
                       else c.end_point1 for c in connections]
            print(f"<{zone_name}>: {' | '.join(targets)}")

    @property
    def start_zone_name(self) -> str:
        """Return the configured start zone name.

        Returns:
            Start zone name.
        """
        return self.get_start()
