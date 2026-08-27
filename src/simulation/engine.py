from typing import Dict
from src.models import Drone, Map
from .pathfinder import PathFinder


class SimulationEngine():
    def __init__(self, sim_map: Map) -> None:
        self._drones: Dict[str, Drone] = {}
        self._running: bool = False
        self._turn: int = 0
        self._map: Map = sim_map
        self._path_finder: PathFinder = PathFinder()

    def register_drone(self, drone: Drone) -> None:
        self._drones[drone.id] = drone

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def reconstruct_path(self, parent: dict, start: str, goal: str) -> list[str]:
        current = goal
        path = []
        
        # If the goal was never reached, return an empty path
        if current not in parent and current != start:
            return []
            
        while current in parent:
            path.append(current)
            current = parent[current]
        
        path.reverse() # Since we walked backwards from goal to start
        return path

    def process_turn(self) -> None:
        for d in self._drones.values():
            self._path_finder.update(d.path)
            p = self._path_finder.dijkstra(self._map._zones, self._map._adj_list, d)
            print("Path:", self.reconstruct_path(
                p, self._map._start_zone.name, self._map._end_zone.name))

        for d in self._drones.values():
            if len(d.path):
                d.position = d.path.pop(0)

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
