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
