from src.models import Drone, Map, Connection
import heapq
import sys
from typing import Dict


class PathFinder():
    def update(self, path):
        pass

    def dijkstra(self, zones, adj_list, drone) -> Dict[str, str]:
        # Simple Dijkstra structure

        src = drone.current_location

        # Min-heap (priority queue) storing pairs of (distance, node)
        priority_queue = []

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
                weight = 2 if zones[neighbor].metadata.zone_type == "restricted" else 1
                # If we found a shorter path to v through u, update it
                if distances[current_node] + weight < distances[neighbor]:
                    distances[neighbor] = distances[current_node] + weight
                    parent[neighbor] = current_node
                    heapq.heappush(priority_queue, (distances[neighbor], neighbor))

        print("Distances dict:", distances)
        print("Parents dict:", parent)
        return parent

    def time_dijkstra(
            self,
            map_graph: Map,
            drone: Drone,
            reservations,
            link_res,
            goal,
            time=0
            ) -> Dict[str, str]:

        def reconstruct_path(parents: dict, start: str, goal: str) -> list[str]:
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

        zones = map_graph.get_zones()
        connections = map_graph.get_conn_list()
        adj_list = map_graph.get_adj_list()
        src = drone.current_location

        # Min-heap (priority queue) storing pairs of (time-space, distance)
        priority_queue = []

        distances = {(src, 0): 0}
        parent = {}
        visited = set()

        # Distance-time from source to itself is 0
        heapq.heappush(priority_queue, (0, 0, src, time))

        # Process the queue until all reachable vertices are finalized
        while priority_queue:
            cost, priority, current_node, current_time = heapq.heappop(priority_queue)
            current_state = (current_node, current_time)
            
            # If this distance not the latest shortest one, skip it
            if cost > distances[(current_node, current_time)]:
                continue

            # We reach goal:
            if current_node == goal:
                break

            # Is there capacity to wait here?:
            wait_state = (current_node, current_time + 1)
            if wait_state not in reservations and wait_state not in visited:
                distances[wait_state] = cost + 1
                heapq.heappush(
                            priority_queue,
                            (
                                cost + 1,
                                priority,
                                current_node,
                                current_time + 1)
                            )
                parent[(current_node, current_time + 1)] = current_state
                visited.add(wait_state)

            # Explore all neighbors of the current vertex
            for conn in adj_list[current_node]:
                neighbor = (conn.end_point2 if conn.end_point2 != current_node
                            else conn.end_point1)
                # If neighbor is blocked, just skip it
                if zones[neighbor].metadata.zone_type == "blocked":
                    continue
                weight = 2 if zones[neighbor].metadata.zone_type == "restricted" else 1
                next_state = (neighbor, current_time + weight)
                
                if next_state in visited:
                    continue

                # When evaluate a next state (neighbor, arrival_time):
                current_occupants = reservations.get(next_state, 0)
                link_users = link_res.get((conn, current_time), 0)
                zone_capacity = zones[neighbor].metadata.max_drones
                link_capacity = conn.max_link_capacity
                if current_occupants >= zone_capacity or link_users >= link_capacity:
                    # Too crowded! This state is truly blocked.
                    continue

                # If not visited, treat as is: 
                if next_state not in distances:
                    distances[next_state] = sys.maxsize 

                # If we found a shorter path to v through u, update it
                if distances[current_state] + weight < distances[next_state]:
                    distances[next_state] = distances[current_state] + weight
                    parent[next_state] = current_state
                    visited.add(next_state)
                    new_priority = (priority - 1 if zones[neighbor].metadata.
                            zone_type == "priority" else priority)
                    heapq.heappush(
                            priority_queue,
                            (
                                distances[next_state], 
                                new_priority, 
                                neighbor, 
                                current_time + weight)
                            )

#        print("Distances dict:", distances)
#        print("Parents dict:", parent)
#        print("reservations:", reservations)
        return reconstruct_path(parent, (src, time), current_state)
