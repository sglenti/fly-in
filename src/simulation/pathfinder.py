from src.models import Drone, Map, Connection, Zone
import heapq
import sys
from typing import Dict, List, Tuple, Set


class PathFinder():
    def update(self) -> None:
        pass

    def dijkstra(
            self,
            zones: Dict[str, Zone],
            adj_list: Dict[str, List[Connection]],
            drone: Drone
            ) -> Dict[str, str] | None:
        if not drone.current_location:
            return None

        # Simple Dijkstra structure
        src = drone.current_location

        # Min-heap (priority queue) storing pairs of (distance, node)
        priority_queue: List[Tuple[int, str]] = []

        distances = {k: sys.maxsize for k in adj_list}
        parent = {}

        # Distance from source to itself is 0
        distances[src] = 0
        heapq.heappush(priority_queue, (0, src))

        # Process the queue until all reachable vertices are finalized
        while priority_queue:
            current_dist, current_node = heapq.heappop(priority_queue)

            # If this distance not the latest shortest one, skip it
            if current_dist > distances[current_node]:
                continue

            # Explore all neighbors of the current vertex
            for conn in adj_list[current_node]:
                neighbor = (conn.end_point2 if conn.end_point2 != current_node
                            else conn.end_point1)
                weight = (2 if zones[neighbor].
                          metadata.zone_type == "restricted" else 1)
                # If we found a shorter path to v through u, update it
                if distances[current_node] + weight < distances[neighbor]:
                    distances[neighbor] = distances[current_node] + weight
                    parent[neighbor] = current_node
                    heapq.heappush(
                            priority_queue, (distances[neighbor], neighbor))

        # print("Distances dict:", distances)
        # print("Parents dict:", parent)
        return parent

    def time_dijkstra(
            self,
            map_graph: Map,
            drone: Drone,
            reservations: Dict[Tuple[str, int], int],
            link_res: Dict[Tuple[Connection, int], int],
            goal: str,
            time: int = 0
            ) -> List[Tuple[str, int]]:

        def heuristic(node_name: str) -> float:
            z = map_graph.get_zones()[node_name]
            goal = map_graph.get_zones()[map_graph.get_end()]
            # Euclidean distance to goal
            return (((z.x - goal.x) ** 2 + (z.y - goal.y) ** 2) ** 0.5) * 1

        def reconstruct_path(
                parents: Dict[Tuple[str, int], Tuple[str, int]],
                start: Tuple[str, int],
                goal: Tuple[str, int]) -> List[Tuple[str, int]]:
            current = goal
            path: List[Tuple[str, int]] = []
            # If the goal was never reached, return an empty path
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
        # connections: List[Connection] = map_graph.get_conn_list()
        adj_list: Dict[str, List[Connection]] = map_graph.get_adj_list()
        src: str = drone.current_location

        # Min-heap (priority queue) storing pairs of (time-space, distance)
        priority_queue: List[Tuple[float, int, float, str, int]] = []

        distances: Dict[Tuple[str, int], int] = {(src, 0): 0}
        parent: Dict[Tuple[str, int], Tuple[str, int]] = {}

        # Distance-time from source to itself is 0
        heapq.heappush(priority_queue, (heuristic(src), 0, 0, src, time))

        # Process the queue until all reachable vertices are finalized
        while priority_queue:
            ec, cost, priority, current_node, current_time = heapq.heappop(
                    priority_queue)
            current_state = (current_node, current_time)

            # If this distance is bigger than latest shortest one, skip it
            if cost > distances[(current_node, current_time)]:
                continue

            # We reach goal:
            if current_node == goal:
                break

            # Is there capacity to wait here?:
            wait_state = (current_node, current_time + 1)
            if wait_state not in reservations:
                distances[wait_state] = cost + 1
                est_cost = distances[wait_state] + heuristic(current_node) - 0.1
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

            # Explore all neighbors of the current vertex
            for conn in adj_list[current_node]:
                neighbor = (conn.end_point2 if conn.end_point2 != current_node
                            else conn.end_point1)
                # If neighbor is blocked, just skip it
                if zones[neighbor].metadata.zone_type == "blocked":
                    continue
                weight = (2 if zones[neighbor].
                          metadata.zone_type == "restricted" else 1)
                next_state = (neighbor, current_time + weight)

                # When evaluate a next state (neighbor, arrival_time):
                current_occupants = reservations.get(next_state, 0)
                link_users = link_res.get((conn, current_time + weight), 0)
                zone_capacity = zones[neighbor].metadata.max_drones
                link_capacity = conn.max_link_capacity
                if (current_occupants >= zone_capacity or
                        link_users >= link_capacity):
                    # Too crowded! This state is alreary fully booked
                    continue

                # If not visited, treat as is:
                if next_state not in distances:
                    distances[next_state] = sys.maxsize

                # If we found a shorter path to v through u, update it
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

        # print("Distances dict:", distances)
        # print("Parents dict:", parent)
        # print("reservations:", reservations)
        return reconstruct_path(parent, (src, time), current_state)
