"""Pathfinding utilities for the drone-routing simulation."""

from src.models import Drone, Map, Connection, Zone
import heapq
import sys
from typing import Dict, List, Tuple


class PathFinder:
    """Compute valid paths through the map while respecting capacity rules.

    The pathfinder supports both plain connectivity checks and time-aware route
    planning that accounts for hub restrictions and link reservations.
    """

    def base_dijkstra(
            self,
            zones: Dict[str, Zone],
            adj_list: Dict[str, List[Connection]],
            src: str,
            goal: str
            ) -> bool:
        """Check whether a valid path exists from source to goal.

        Args:
            zones: Mapping of zone names to zone definitions.
            adj_list: Adjacency list for the map graph.
            src: Source zone name.
            goal: Goal zone name.

        Returns:
            ``True`` if a path exists, otherwise ``False``.
        """
        priority_queue: List[Tuple[int, str]] = []
        distances = {k: sys.maxsize for k in adj_list}

        distances[src] = 0
        heapq.heappush(priority_queue, (0, src))

        while priority_queue:
            current_dist, current_node = heapq.heappop(priority_queue)

            if current_dist > distances[current_node]:
                continue

            if current_node == goal:
                return True

            for conn in adj_list[current_node]:
                neighbor = (conn.end_point2 if conn.end_point2 != current_node
                            else conn.end_point1)
                if zones[neighbor].metadata.zone_type == "blocked":
                    continue
                weight = (2 if zones[neighbor].
                          metadata.zone_type == "restricted" else 1)
                if distances[current_node] + weight < distances[neighbor]:
                    distances[neighbor] = distances[current_node] + weight
                    heapq.heappush(
                            priority_queue, (distances[neighbor], neighbor))

        return False

    def time_dijkstra(
            self,
            map_graph: Map,
            drone: Drone,
            reservations: Dict[Tuple[str, int], int],
            link_res: Dict[Tuple[Connection, int], int],
            goal: str,
            time: int = 0,
            heur: bool = False
            ) -> List[Tuple[str, int]]:
        """Compute a time-aware route for a drone using reservation-aware Dijkstra.

        Args:
            map_graph: Current map graph.
            drone: Drone whose route is being planned.
            reservations: Zone-time occupancy reservations.
            link_res: Connection-time reservations.
            goal: Goal zone name.
            time: Current simulation time offset.
            heur: Whether to add a heuristic value to the priority queue.

        Returns:
            A list of ``(zone_name, turn)`` steps describing the route.
        """
        def heuristic(node_name: str) -> float:
            """Calculate a simple heuristic distance to the goal.

            Args:
                node_name: Name of the node to evaluate.

            Returns:
                Euclidean distance to the goal when heuristics are enabled,
                otherwise ``0.0``.
            """
            if not heur:
                return float(0)
            z = map_graph.get_zones()[node_name]
            goal_zone = map_graph.get_zones()[map_graph.get_end()]
            return float(((z.x - goal_zone.x) ** 2 + (z.y - goal_zone.y) ** 2) ** 0.5)

        def reconstruct_path(
                parents: Dict[Tuple[str, int], Tuple[str, int]],
                start: Tuple[str, int],
                goal_state: Tuple[str, int]) -> List[Tuple[str, int]]:
            """Reconstruct the route from predecessor links.

            Args:
                parents: Mapping of a state to its predecessor state.
                start: Starting state.
                goal_state: Final reachable state.

            Returns:
                The route from start to goal, expressed as ``(zone, turn)`` pairs.
            """
            current = goal_state
            path: List[Tuple[str, int]] = []
            if current not in parent and current != start:
                return []

            while current in parent:
                path.append(current)
                current = parent[current]

            path.reverse()
            return path

        if not drone.current_location:
            return []
        zones: Dict[str, Zone] = map_graph.get_zones()
        adj_list: Dict[str, List[Connection]] = map_graph.get_adj_list()
        src: str = drone.current_location

        priority_queue: List[Tuple[float, int, float, str, int]] = []

        distances: Dict[Tuple[str, int], int] = {(src, 0): 0}
        parent: Dict[Tuple[str, int], Tuple[str, int]] = {}

        heapq.heappush(priority_queue, (heuristic(src), 0, 0, src, time))

        while priority_queue:
            ec, cost, priority, current_node, current_time = heapq.heappop(
                    priority_queue)
            current_state = (current_node, current_time)

            if cost > distances[(current_node, current_time)]:
                continue

            if current_node == goal:
                break

            wait_state = (current_node, current_time + 1)
            if wait_state not in reservations:
                distances[wait_state] = cost + 1
                est_cost = (
                        distances[wait_state] + heuristic(current_node) - 0.1)
                heapq.heappush(
                            priority_queue,
                            (
                                est_cost,
                                distances[wait_state],
                                priority - 0.01,
                                current_node,
                                current_time + 1)
                            )
                parent[(current_node, current_time + 1)] = current_state

            for conn in adj_list[current_node]:
                neighbor = (conn.end_point2 if conn.end_point2 != current_node
                            else conn.end_point1)
                if zones[neighbor].metadata.zone_type == "blocked":
                    continue
                weight = (2 if zones[neighbor].
                          metadata.zone_type == "restricted" else 1)
                next_state = (neighbor, current_time + weight)

                current_occupants = reservations.get(next_state, 0)
                link_users = link_res.get((conn, current_time + 1), 0)
                zone_capacity = zones[neighbor].metadata.max_drones
                link_capacity = conn.max_link_capacity
                if (current_occupants >= zone_capacity or
                        link_users >= link_capacity):
                    continue
                if weight == 2:
                    link_users = link_res.get((conn, current_time + 2), 0)
                if link_users >= link_capacity:
                    continue

                if next_state not in distances:
                    distances[next_state] = sys.maxsize

                if distances[current_state] + weight < distances[next_state]:
                    distances[next_state] = distances[current_state] + weight
                    parent[next_state] = current_state
                    new_priority = (priority - 1 if zones[neighbor].metadata.
                                    zone_type == "priority" else priority)
                    est_cost = distances[next_state] + heuristic(neighbor)
                    if neighbor == parent.get(current_state, (None, 0))[0]:
                        est_cost += 1
                    heapq.heappush(
                            priority_queue,
                            (
                                est_cost,
                                distances[next_state],
                                new_priority,
                                neighbor,
                                current_time + weight)
                            )
        return reconstruct_path(parent, (src, time), current_state)
