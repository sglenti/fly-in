from typing import Dict, Tuple, List
from src.models import Drone, Map, Connection, DroneStatus
from .pathfinder import PathFinder


class SimulationEngine():
    def __init__(self, sim_map: Map) -> None:
        self._drones: Dict[str, Drone] = {}
        self._running: bool = False
        self._turn: int = 0
        self._map: Map = sim_map
        self._path_finder: PathFinder = PathFinder()
        self._reservations: Dict[Tuple[str, int], int] = {}
        self._link_res: Dict[Tuple[Connection, int], int] = {}
        self._nb_drones: int
        self._turn_moves: List[str]

    def register_drone(self, drone: Drone) -> None:
        self._drones[drone.id] = drone

    def set_nb_drones(self, nb_drones: int) -> None:
        self._nb_drones = nb_drones

    def get_nb_drones(self) -> int:
        return self._nb_drones

    def get_turn_moves(self) -> List[str]:
        return self._turn_moves

    def get_drones(self) -> Dict[str, Drone]:
        return self._drones

    def get_turn(self) -> int:
        return self._turn

    def get_link_res(self) -> Dict[Tuple[Connection, int], int]:
        return self._link_res

    def check_connectivity(self) -> None:
        if not self._path_finder.base_dijkstra(
                self._map.get_zones(),
                self._map.get_adj_list(),
                self._map.get_start(),
                self._map.get_end()
                ):
            raise RuntimeError(
                "Critical error: unable to find a path between start and goal")

    def calculate_paths(self, heuristics: bool) -> None:
        for d in self._drones.values():
            d.path = self._path_finder.time_dijkstra(
                        self._map,
                        d,
                        self._reservations,
                        self._link_res,
                        self._map.get_end(),
                        heur=heuristics
                    )
            start: str = self._map.get_start()
            end: str = self._map.get_end()
            current_pos = start

            for node in d.path:
                # zone-time reservations:
                target_node = node[0]
                time_step = node[1]
                if (target_node != start and target_node != end):
                    self._reservations[
                            node] = self._reservations.get(node, 0) + 1

                # link-time reservations:
                conn = self._map.get_connection(current_pos, target_node)
                if conn:
                    edge: Tuple[Connection, int] = (conn, time_step)
                    self._link_res[edge] = self._link_res.get(edge, 0) + 1
                    # if moving into a restricted zone, reserve 2 turns
                    if self._map.is_restricted(target_node):
                        edge = (conn, time_step - 1)
                        self._link_res[edge] = self._link_res.get(edge, 0) + 1
                current_pos = target_node

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def _validate_moves(self) -> None:
        intents_zone: Dict[Tuple[str, int], List[str]] = {}
        intents_conn: Dict[Tuple[Connection, int], List[str]] = {}

        for d in self._drones.values():
            if not d.path:
                # Drone arrived
                continue
            if d.current_location:
                # Docked drone
                node = d.path[0]
                if node not in intents_zone:
                    intents_zone[node] = []
                intents_zone[node].append(d.id)
                # if it is moving, check link
                if node[0] != d.current_location:
                    conn = self._map.get_connection(
                            d.current_location, node[0])
                    if not conn:
                        raise RuntimeError(
                            f"Invalid movement (turn {self._turn}): "
                            f"no connection ({d.current_location}-{node[0]})")
                    edge: Tuple[Connection, int] = (conn, node[1])
                    if edge not in intents_conn:
                        intents_conn[edge] = []
                    intents_conn[edge].append(d.id)
                    # if we have a 2 turn movement, need to reserve for both
                    if node[1] == self._turn + 1:
                        edge = (conn, node[1] - 1)
                        if edge not in intents_conn:
                            intents_conn[edge] = []
                        intents_conn[edge].append(d.id)
                # Also check next location if it happens next turn
                if len(d.path) > 1 and d.path[1][1] == self._turn + 1:
                    node = d.path[1]
                    if node not in intents_zone:
                        intents_zone[node] = []
                    intents_zone[node].append(d.id)
            else:
                # Drone in transit:
                node = d.path[0]
                if node not in intents_zone:
                    intents_zone[node] = []
                intents_zone[node].append(d.id)
                if len(d.path) > 1 and d.path[1][1] == self._turn + 1:
                    node = d.path[1]
                    if node not in intents_zone:
                        intents_zone[node] = []
                    intents_zone[node].append(d.id)

        zones = self._map.get_zones()
        for iz, drones in intents_zone.items():
            zone = iz[0]
            if zone == self._map.get_start() or zone == self._map.get_end():
                continue
            if len(drones) > zones[zone].metadata.max_drones:
                raise RuntimeError(
                    f"Hub '{zone}' Max Capacity Violation (turn {self._turn})")
            elif zones[zone].metadata.zone_type == "blocked":
                raise RuntimeError(
                   f"Trying to enter Blocked Hub '{zone}' (turn {self._turn})")
        for ic, drones in intents_conn.items():
            conn = ic[0]
            if len(drones) > conn.max_link_capacity:
                raise RuntimeError(
                        f"Link Capacity Violation (turn {self._turn}): "
                        f"'{ic[0]}:{drones}'")

    def process_turn(self) -> None:
        self._turn += 1
        self._turn_moves = []

        # sanity check, will raise an exception for invalid moves
        self._validate_moves()

        # Paths validated, drones can move:
        for d in self._drones.values():
            if len(d.path) and d.status != DroneStatus.DELIVERED:
                if d.path[0][1] == self._turn:
                    # Drone arriving (or waiting) this turn:
                    if d.path[0][0] == d.current_location:
                        d.status = DroneStatus.WAITING
                    elif d.current_location is None:
                        d.status = DroneStatus.IN_TRANSIT
                    else:
                        d.status = DroneStatus.MOVING
                    d.current_location = d.path.pop(0)[0]
                    if d.status != DroneStatus.WAITING:
                        self._turn_moves.append(f"{d.id}-{d.current_location}")

                elif d.path[0][1] == self._turn + 1:
                    # Drone in transit to restricted zone:
                    end1 = d.current_location
                    end2 = d.path[0][0]
                    d.current_location = None
                    d.status = DroneStatus.IN_TRANSIT
                    self._turn_moves.append(f"{d.id}-{end1}-{end2}")
                else:
                    # Houston, we have a problem:
                    raise ValueError(
                        f"Drone '{d.id}' with path node in the past!"
                        f"{d.path}")
            else:
                d.status = DroneStatus.DELIVERED

    def calculate_all_occupancies(self) -> Dict[str, int]:
        return {z: sum(z == d.current_location for d in self._drones.values())
                for z in self._map.get_zones()}
