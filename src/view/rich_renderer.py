from rich.console import Console
from rich.table import Table
from src.models import Map, Drone
from typing import Dict


class ConsoleRenderer:
    def __init__(self, map_graph: Map) -> None:
        self.console = Console()
        self.map_graph = map_graph

    def render_map_info(self, drones: Dict[str, Drone]) -> None:
        table = Table(title="Map Topology")
        table.add_column("Zone")
        table.add_column("Type")
        table.add_column("Neighbors")
        table.add_column("Max")
        table.add_column("Drones")
        
        # logic to loop through map._adj_list and add rows...
        for node in self.map_graph._zones.values():
            neighbors = [c.target_name if c.source_name == node.name 
                else c.source_name for c in self.map_graph._adj_list[node.name]]
            table.add_row(
                    node.name,
                    node.metadata.zone_type,
                    ",".join(neighbors),
                    str(node.metadata.max_drones),
                    ",".join([d.id for d in filter(
                        lambda d: d.current_location == node.name,drones.values())])
                    )
        self.console.print(table)
