from models import Map, Zone, Connection, ZoneMetadata, Drone
from simulation import SimulationEngine
from typing import Dict, Any, List
from pydantic import ValidationError


class Parser():

    def __init__(self, map_graph: Map, engine: SimulationEngine) -> None:
        self._map_graph = map_graph
        self._engine = engine

    def parse_file(self, file_name: str) -> None:
        def create_zone(data_str: str) -> Zone:
            data, meta = data_str.split(" [", 1)
            values = data.split(" ", 3)
            if len(values) != 3:
                if values[1].isalpha():
                    raise ValueError(
                        f"Name cannot contain spaces, '{values[0]} {values[1]}'")
                else:
                    raise SyntaxError(
                        f"Wrong syntax for map file, hub '{values[0]}'"
                        "\n Format: 'name x y \[optional metadata]'")
            metadata = None
            if meta:
                if not meta.endswith("]"):
                    raise SyntaxError(
                        f"Wrong syntax for map file, hub '{values[0]}'")
                items = meta.strip("]").split()
                params: Dict[str, str] = {}
                for item in items:
                    key_value: List[Any] = item.split("=")
                    if len(key_value) != 2:
                        raise SyntaxError(
                            f"Wrong map file syntax, hub {values[0]}: {item}")
                    if key_value[1].isdigit():
                        key_value[1] = int(key_value[1])
                    params[key_value[0]] = key_value[1]
                if 'zone' in params:
                    params['zone_type'] = params.pop('zone')
                metadata = ZoneMetadata(**params)
            return Zone(
                name=values[0], x=values[1], y=values[2], metadata=metadata)

        def create_connection(data: str) -> Connection:
            values: List[str] = data.split(" [", 1)
            if len(values) > 2:
                raise SyntaxError(
                        f"Wrong syntax for Connection"
                        "\n Format: zone1-zone2 \[optional metadata]")
            hubs: List[str] = values[0].split("-")
            if len(hubs) != 2:
                raise ValueError(f"Wrong connection format: '{values[0]}'")
            valid_names = self._map_graph.get_zones().keys()
            #for hub in hubs:
            #    if hub not in valid_names:
            #        raise ValueError(
            #                f"Invalid Zone name for Connection: '{hub}'")
            params: Dict[str, str | int] = {
                    "end_point1": hubs[0], "end_point2": hubs[1]}
            if len(values) == 2:
                meta = values[1]
                if not meta.endswith("]"):
                    raise SyntaxError(
                        f"Wrong syntax for connection metadata '{values[0]}'")
                key, value = values[1].strip("[]").split("=")
                params[key] = int(value)
            return Connection(**params)

        with open(file_name) as file:
            content = [line.strip() for line in file]
        if not content:
            raise SyntaxError("Empty map file")

        for i, line in enumerate(content, 1):
            if line.startswith('#') or not len(line):
                continue
            first_line = line.split(": ")
            if first_line[0] == "nb_drones" and len(first_line) == 2:
                nb_dr_msg = f"Value error, nb_drones must be a positive integer"
                try:
                    nb_drones = int(first_line[1])
                except ValueError:
                    raise ValueError(nb_dr_msg)
                if nb_drones <= 0: 
                    raise ValueError(nb_dr_msg)
                self._engine.set_nb_drones(nb_drones)
            else:
                raise SyntaxError("Wrong syntax for map file, "
                                  "line 1 must specify 'nb_drones: <nb>'")
            break

        for n, line in enumerate(content[i:], i + 1):
            if line.startswith('#') or not len(line):
                continue
            parsed_line = line.split(": ")
            if len(parsed_line) != 2:
                raise SyntaxError(f"Wrong syntax for map file, line {n}")
            elif "hub" in parsed_line[0]:
                hub_keys: List[str] = ["start_hub", "end_hub", "hub"]
                if parsed_line[0] in hub_keys:
                    try:
                        zone = create_zone(parsed_line[1])
                    except ValidationError as ve:
                        error = ve.errors()[0]
                        field = " -> ".join(str(loc) for loc in error["loc"])
                        raise ValueError(
                            f"Error in line {n}: '{field}' {error['msg']}")
                    except Exception as e:
                        raise ValueError(
                            f"Error in line {n}: {e}")
                    self._map_graph.add_zone(zone)
                    if parsed_line[0] == "start_hub":
                        self._map_graph.set_start_zone(zone)
                    elif parsed_line[0] == "end_hub":
                        self._map_graph.set_end_zone(zone)
                else:
                    print(parsed_line)
                    raise SyntaxError(
                            f"Wrong hub syntax, line {n}"
                            f"\n Valid keys are {hub_keys}")
            elif parsed_line[0] == "connection":
                try:
                    conn = create_connection(parsed_line[1])
                except Exception as e:
                    raise ValueError(
                            f"Error in line {n}: {e}")
                self._map_graph.add_connection(conn)
            elif parsed_line[0] == "nb_drones":
                raise SyntaxError(
                            f"Wrong syntax for map file, line: '{n}'"
                            "\n nb_drones can't be defined twice")
            else:
                raise SyntaxError(
                    f"Error in line {n}: invalid key '{parsed_line [0]}'")

        for i in range(1, nb_drones + 1):
            self._engine.register_drone(
                Drone(id=f"D{i:0{len(str(nb_drones))}d}",
                      current_location=self._map_graph.start_zone_name))


"""
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
        # --- The "Bootstrap" Loop ---
        # 1. Fill Zones
        for zone in self.zones_to_add.values():
            self._map_graph.add_zone(zone)

        # 2. Fill Connections
        for src, dst in self.connections_to_add:
            # Notice how we create the Connection object on the fly
            conn = Connection(source_name=src, target_name=dst)
            self._map_graph.add_connection(conn)

"""
