from models import Map, Zone, Connection, ZoneMetadata, ZoneType


class Parser():
    # The Zones (name as key, object as value)
    zones_to_add = {
        "start": Zone(name="start", x=0, y=0),
        "mid": Zone(name="mid", x=5, y=5,
                    metadata=ZoneMetadata(zone_type=ZoneType.RESTRICTED)),
        "end": Zone(name="end", x=10, y=10)
    }

    # The Connections (as a list of tuples)
    connections_to_add = [
        ("start", "mid"),
        ("mid", "end")
    ]

    def __init__(self, map_graph: Map) -> None:
        self._map_graph = map_graph

    def parse_file(self, file_name: str) -> None:
        # TODO: read first line and record number of drones

        # --- The "Bootstrap" Loop ---
        # 1. Fill Zones
        for zone in self.zones_to_add.values():
            self._map_graph.add_zone(zone)

        # 2. Fill Connections
        for src, dst in self.connections_to_add:
            # Notice how we create the Connection object on the fly
            conn = Connection(source_name=src, target_name=dst)
            self._map_graph.add_connection(conn)
