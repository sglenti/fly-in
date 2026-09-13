from models import Map, Zone, Connection, ZoneMetadata, Drone
from simulation import SimulationEngine
from typing import Dict, Any, List
from pydantic import ValidationError
import re


class Parser():

    def __init__(self, map_graph: Map, engine: SimulationEngine) -> None:
        self._map_graph = map_graph
        self._engine = engine

    def parse_file(self, file_name: str) -> None:
        def create_zone(data_str: str) -> Zone:
            data_meta = data_str.split(" [", 1)
            values = data_meta[0].split(" ")
            meta = data_meta[1] if len(data_meta) == 2 else None
            if len(values) != 3:
                if values[1].isalpha():
                    raise ValueError(
                        f"Name cannot contain space, '{values[0]} {values[1]}'")
                else:
                    raise SyntaxError(
                        f"Wrong syntax for map file, hub '{values[0]}'"
                        "\n Format: 'name x y [optional metadata]'")
            metadata = None
            if meta:
                if not meta.endswith("]"):
                    raise SyntaxError(
                        f"Wrong syntax (missing bracket), hub '{values[0]}'")
                meta = meta[:-1]
                if "[" in meta or "]" in meta:
                    raise SyntaxError(
                        f"Wrong syntax (too many brackets), hub '{values[0]}'")
                items = meta.split()
                params: Dict[str, str] = {}
                valid_keys = ["zone", "color", "max_drones"]
                for item in items:
                    key_value: List[Any] = item.split("=")
                    if len(key_value) != 2:
                        raise SyntaxError(
                            f"Wrong hub metadata syntax '{item}'"
                            "\n Format: '[key=value ...]'")
                    if key_value[0] not in valid_keys:
                        raise SyntaxError(
                            f"Invalid key for hub metadata '{item}'"
                            f"\n Valid keys: {valid_keys}")
                    if key_value[0] in params:
                        raise SyntaxError(
                            f"Wrong hub metadata syntax"
                            f"\n '{key_value[0]}' cannot be defined twice")
                    if key_value[1].isdigit():
                        key_value[1] = int(key_value[1])
                    params[key_value[0]] = key_value[1]
                if 'zone' in params:
                    params['zone_type'] = params.pop('zone')
                metadata = ZoneMetadata(**params)
            return Zone(
                name=values[0], x=values[1], y=values[2], metadata=metadata)

        def create_connection(data: str) -> Connection:
            values: List[str] = data.split(" [")
            hubs: List[str] = values[0].split("-")
            if len(hubs) != 2 or len(values) > 2 or " " in values[0]:
                raise SyntaxError(
                        f"Wrong connection format: '{values[0]}'"
                        "\n Format: 'zone1-zone2 [optional metadata]'")
            valid_names = self._map_graph.get_zones().keys()
            for hub in hubs:
                if hub not in valid_names:
                    raise ValueError(
                            f"Invalid Zone name for Connection: '{hub}'")
            params: Dict[str, str | int] = {
                    "end_point1": hubs[0], "end_point2": hubs[1]}
            if len(values) == 2:
                meta = values[1]
                if not meta.endswith("]"):
                    raise SyntaxError(
                        f"Missing end bracket, connection metadata '{meta}'")
                meta = meta[:-1]
                if "[" in meta or "]" in meta:
                    raise SyntaxError(
                        f"Too many brackets, connextion metadata '{meta}'")
                if " " in meta:
                    raise SyntaxError(
                        f"No spaces allowed in connextion metadata '{meta}'")
                conn_max = meta.split("=")
                if len(conn_max) != 2:
                    raise SyntaxError(
                        f"Wrong format for connection metadata '{meta}'"
                        "\n Format: '[max_link_capacity=<nb>]'")
                key, value = conn_max
                if key != "max_link_capacity":
                    raise SyntaxError(
                        f"Wrong metadata key '{key}'"
                        "\n Format: '[max_link_capacity=<nb>]'")
                try:
                    params[key] = int(value)
                except ValueError as e:
                    raise ValueError(
                        "Value error, "
                        "max_link_capacity must be a positive integer")
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
                        clean = re.sub(r'\s+', ' ', parsed_line[1].strip())
                        zone = create_zone(clean)
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
                    raise SyntaxError(
                            f"Wrong hub syntax, line {n}"
                            f"\n Valid keys are {hub_keys}")
            elif parsed_line[0] == "connection":
                try:
                    clean = re.sub(r'\s+', ' ', parsed_line[1].strip())
                    conn = create_connection(clean)
                except ValidationError as ve:
                    error = ve.errors()[0]
                    field = " -> ".join(str(loc) for loc in error["loc"])
                    raise ValueError(
                        f"Error in line {n}: '{field}' {error['msg']}")
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
