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
                neighbor = (conn.target_name if conn.target_name != current_node
                            else conn.source_name)
                weight = 2 if zones[neighbor].metadata.zone_type == "restricted" else 1
                # If we found a shorter path to v through u, update it
                if distances[current_node] + weight < distances[neighbor]:
                    distances[neighbor] = distances[current_node] + weight
                    parent[neighbor] = current_node
                    heapq.heappush(priority_queue, (distances[neighbor], neighbor))

        print("Distances dict:", distances)
        print("Parents dict:", parent)
        return parent

    def time_dijkstra(self, zones, adj_list, drone, reservations, goal, time=0
                      ) -> Dict[str, str]:

        def reconstruct_path(parents: dict, start: str, goal: str) -> list[str]:
            current = goal
            path = []
            print("############", parents)
            # If the goal was never reached, return an empty path
            if current not in parent and current != start:
                return []
                
            while current in parent:
                path.append(current)
                current = parent[current]
            
            path.reverse() # Since we walked backwards from goal to start
            return path

        src = drone.current_location

        # Min-heap (priority queue) storing pairs of (time-space, distance)
        priority_queue = []

        distances = {(src, 0): 0}
        parent = {}
        visited = []

        # Distance-time from source to itself is 0
        heapq.heappush(priority_queue, (0, src, time))

        # Process the queue until all reachable vertices are finalized
        while priority_queue:
            cost, current_node, current_time = heapq.heappop(priority_queue)
            current_state = (current_node, current_time)
            
            # If this distance not the latest shortest one, skip it
            if cost > distances[(current_node, current_time)]:
                continue

            if current_node == goal:
                break
            
            if (current_node, current_time + 1) not in reservations:
                distances[(current_node, current_time + 1)] = cost + 1
                heapq.heappush(
                            priority_queue,
                            (cost + 1, current_node, current_time + 1)
                            )
                parent[(current_node, current_time + 1)] = current_state

            # Explore all neighbors of the current vertex
            for conn in adj_list[current_node]:
                neighbor = (conn.target_name if conn.target_name != current_node
                            else conn.source_name)
                weight = 2 if zones[neighbor].metadata.zone_type == "restricted" else 1
                next_state = (neighbor, current_time + weight)
                
                if next_state in visited:
                    continue
                
                # When evaluate a next state (neighbor, arrival_time):
                if next_state in reservations:
                    # Impassable! Treat it as a wall.
                    continue
                # If not visited, treat as is: 
                if next_state not in distances:
                    distances[next_state] = sys.maxsize 
               
                # If we found a shorter path to v through u, update it
                if distances[current_state] + weight < distances[next_state]:
                    distances[next_state] = distances[current_state] + weight
                    parent[next_state] = current_state
                    visited.append(next_state)
                    heapq.heappush(
                            priority_queue,
                            (distances[next_state], neighbor, current_time + weight)
                            )

#        print("Distances dict:", distances)
#        print("Parents dict:", parent)
#        print("reservations:", reservations)
        return reconstruct_path(parent, (src, time), current_state)
