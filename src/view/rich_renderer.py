from rich.console import Console
from rich.table import Table
from rich.live import Live
from src.models import Map, Drone
from typing import Dict


class ConsoleRenderer:
    def __init__(self, map_graph: Map) -> None:
        self._console = Console()
        self.map_graph = map_graph
        self._live: Live = None
    
    def start_session(self) -> None:
        """Starts the live terminal display session."""
        self._live = Live(auto_refresh=False)
        self._live.start()

    def end_session(self) -> None:
        """Stops the live terminal display session."""
        if self._live:
            self._live.stop()

    def render_turn(self, turn: int, drones: Dict[str, Drone]) -> None:
        """Updates the table in place without breaking headless logic."""
        # table = self._generate_table(turn, drones)
        table = self.render_map_info(turn, drones)
        # Update what the Live display is showing
        if self._live:
            self._live.update(table)
            self._live.refresh()
        else:
            self._console.print(table)

    def render_map_info(self, turn: int, drones: Dict[str, Drone]) -> Table:
        table = Table(title="Map Topology")
        table.add_column("Zone")
        table.add_column("Type")
        table.add_column("Neighbors")
        table.add_column("Max")
        table.add_column("Drones")
        
        # logic to loop through map._adj_list and add rows...
        for node in self.map_graph._zones.values():
            neighbors = [c.end_point2 if c.end_point1 == node.name 
                else c.end_point1 for c in self.map_graph._adj_list[node.name]]
            table.add_row(
                    node.name,
                    node.metadata.zone_type,
                    ",".join(neighbors),
                    str(node.metadata.max_drones),
                    ",".join([d.id for d in filter(
                        lambda d: d.current_location == node.name,drones.values())])
                    )
        return table
