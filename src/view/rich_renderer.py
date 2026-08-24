from rich.console import Console
from rich.table import Table
from src.models import Map

class ConsoleRenderer:
    def __init__(self, map_graph: Map) -> None:
        self.console = Console()
        self.map_graph = map_graph

    def render_map_info(self) -> None:
        table = Table(title="Map Topology")
        table.add_column("Zone")
        table.add_column("Type")
        table.add_column("Neighbors")
        
        # logic to loop through map._adj_list and add rows...
        self.console.print(table)
