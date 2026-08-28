from typing import Dict, Tuple
from src.models import Drone, Map
from .pathfinder import PathFinder


class SimulationEngine():
    def __init__(self, sim_map: Map) -> None:
        self._drones: Dict[str, Drone] = {}
        self._running: bool = False
        self._turn: int = 0
        self._map: Map = sim_map
        self._path_finder: PathFinder = PathFinder()
        self._reservations: Dict[Tuple[str, int], int] = {}

    def register_drone(self, drone: Drone) -> None:
        self._drones[drone.id] = drone

    def start(self) -> None:
        for d in self._drones.values():
            d.path = self._path_finder.time_dijkstra(self._map._zones,
                                                self._map._adj_list,
                                                d,
                                                self._reservations,
                                                self._map._end_zone.name)
            for node in d.path:
                if (node[0] != self._map._start_zone.name and
                    node[0] != self._map._end_zone.name):
                    self._reservations[node] = self._reservations.get(node, 0) + 1

        self._running = True

    def stop(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def process_turn(self) -> None:
        for d in self._drones.values():
            print(f"{d.id} Path:", d.path)
            if len(d.path):
                d.current_location = d.path.pop(0)[0]
        self._turn += 1

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
