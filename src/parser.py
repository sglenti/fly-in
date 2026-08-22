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
        def create_zone(data: str) -> Zone:
            values = data.split(" ", 3)
            if len(values) < 3:
                raise SyntaxError(f"Wrong syntax for map file, hub {values[0]}")
            metadata = None
            if len(values) == 4:
                items = values[3].strip("[]").split()
                params: Dict[str, str] = {}
                for item in items:
                    key_value = item.split("=")
                    if len(key_value) != 2:
                        raise SyntaxError(
                            f"Wrong map file syntax, huh {values[0]}: {item}")
                    if key_value[1].isdigit():
                        key_value[1] = int(key_value[1])
                    params[key_value[0]] = key_value[1]
                if 'zone' in params:
                    params['zone_type'] = params.pop('zone')
                metadata = ZoneMetadata(**params)
            return Zone(name=values[0], x=values[1], y=values[2], metadata=metadata)

        def create_connection(data: str) -> Connection:
            values = data.split()
            if len(values) > 2:
                raise SyntaxError(f"Wrong syntax for map file, conn {values[0]}")
            hubs = values[0].split("-")
            if len(hubs) != 2:
                raise ValueError(f"Wrong connection format: {values[0]}")
            params = {"source_name": hubs[0], "target_name": hubs[1]}
            if len(values) == 2:
                key, value = values[1].strip("[]").split("=")
                params[key] = int(value)
            return Connection(**params)

        with open(file_name) as file:
            content = [line.strip() for line in file if line.strip()
                    and not line.startswith('#')]
        if not content:
            raise SyntaxError("Empty map file")
        
        first_line = content[0].split(": ")
        if first_line[0] == "nb_drones":
            nb_drones = int(first_line[1])
        else:
            raise SyntaxError(f"Wrong syntax for map file, line 1")

        for n, line in enumerate(content[1:], 2):
            parsed_line = line.split(": ")
            if len(parsed_line) != 2:
                raise SyntaxError(f"Wrong syntax for map file, line {n}")
            elif "hub" in parsed_line[0]:
                if parsed_line[0] in ["start_hub", "end_hub", "hub"]:
                    zone = create_zone(parsed_line[1])
                    self._map_graph.add_zone(zone)
                    if parsed_line[0] == "start_hub":
                        self._map_graph.set_start_zone(zone)
                    elif parsed_line[0] == "end_hub":
                        self._map_graph.set_end_zone(zone)
                else:
                    print(parsed_line)
                    raise SyntaxError(f"Wrong syntax for map file, hub line {n}")
            elif parsed_line[0].startswith("connection"):
                conn = create_connection(parsed_line[1])
                self._map_graph.add_connection(conn)
            else:
                raise SyntaxError(f"Wrong key for map file, line {n}")
        return
        
        # --- The "Bootstrap" Loop ---
        # 1. Fill Zones
        for zone in self.zones_to_add.values():
            self._map_graph.add_zone(zone)

        # 2. Fill Connections
        for src, dst in self.connections_to_add:
            # Notice how we create the Connection object on the fly
            conn = Connection(source_name=src, target_name=dst)
            self._map_graph.add_connection(conn)
