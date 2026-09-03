from typing import Dict, Tuple
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

    def register_drone(self, drone: Drone) -> None:
        self._drones[drone.id] = drone

    def set_nb_drones(self, nb_drones: int) -> None:
        self._nb_drones = nb_drones

    def get_nb_drones(self) -> int:
        return self._nb_drones

    def get_drones(self) -> Dict[str, Drone]:
        return self._drones

    def get_turn(self) -> int:
        return self._turn

    def get_link_res(self) -> Dict[Tuple[Connection, int], int]:
        return self._link_res

    def calculate_paths(self) -> None:
        for d in self._drones.values():
            d.path = self._path_finder.time_dijkstra(
                        self._map,
                        d,
                        self._reservations,
                        self._link_res,
                        self._map._end_zone.name)
            start = self._map.get_start()
            end = self._map.get_end()
            current_pos = start
            
            for node in d.path:
                target_node = node[0]
                time_step = node[1]
                if (target_node != start and target_node != end):
                    self._reservations[node] = self._reservations.get(node, 0) + 1
            
                conn = self._map.get_connection(current_pos, target_node)
                if conn:
                    edge = (conn, time_step - 1)
                    self._link_res[edge] = self._link_res.get(edge, 0) + 1
                current_pos = target_node

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def process_turn(self) -> None:
        self._turn += 1
        for d in self._drones.values():
            print(f"{d.id} Path:", d.path)
            if len(d.path) and d.status is not "delivered":
                if d.path[0][1] == self._turn:
                    # Drone arrive at new node:
                    if d.path[0][0] == d.current_location:
                        d.status = DroneStatus.WAITING
                    else:
                        d.status = DroneStatus.MOVING
                    d.current_location = d.path.pop(0)[0]

                elif d.path[0][1] == self._turn + 1:
                    # Drone in transit to restricted zone:
                    d.current_location = None
                    d.status = DroneStatus.IN_TRANSIT
                else:
                    # Houston, we have a problem:
                    raise ValueError("Drone with path node in the past!")
            else:
                d.status = DroneStatus.DELIVERED

    def calculate_all_occupancies(self) -> Dict[str, int]:
        return {z: sum(z == d.current_location for d in self._drones.values())
                for z in self._map.get_zones()}

"""
For every turn, you should split it into three phases:

    Intent Phase (The "Think"):
        Iterate over every drone.
        Ask the Pathfinder: "Given the current map and the positions of all other drones, what is your next best move?"
        Store these "Intents" in a temporary structure (e.g., a dictionary drone_id -> target_zone).
        Crucial: Do not update the drone's actual position yet!

    Conflict Resolution Phase (The "Traffic Control"):
        Check the requested "Intents" against the max_drones and max_link_capacity rules.
        If two drones want to move into the same zone, resolve the conflict (e.g., let the higher-priority drone move and force the other to wait).

    Commit Phase (The "Act"):
        Update the drone positions for all confirmed moves.
        Log the turn using the mandatory output format.
"""
