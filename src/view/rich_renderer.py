from rich.console import Console
from rich.layout import Layout
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich import box
from src.models import Map, Drone
from typing import Dict, List


class ConsoleRenderer:
    def __init__(self, map_graph: Map) -> None:
        self._console = Console()
        self.map_graph = map_graph
        self._live: Live = None
        self._layout = Layout()
        self.log_history = []
        self._layout.split_column(
            Layout(name="upper", size=(len(self.map_graph.get_zones()) + 5)),
            # Layout(name="upper",  ),
            Layout(name="lower")
        )
    
    def start_session(self) -> None:
        """Starts the live terminal display session."""
        # Initial empty table:
        table = self.render_map_info(0, {})
        self._layout["upper"].update(table)
        self._layout["lower"].update(Panel("Simulation starting...", title="Turn Log"))
        self._live = Live(self._layout, console=self._console,
                auto_refresh=False)
        self._live.start()

    def end_session(self) -> None:
        """Stops the live terminal display session."""
        if self._live:
            self._live.stop()

    def print_line(self, turn: int, moves: List[str]) -> None:
        # self._console.print(f"Turn {turn}:", occupancy_map)
        # self._live.refresh()
        # return
        move_log_string = f"Turn {turn}: {' '.join(moves)}"
        self.log_history.append(move_log_string)
        recent_logs = "\n".join(self.log_history[-50:])  # Last 10 lines
        # Wrap in Text
        text_obj = Text(recent_logs)
    
        # Align to bottom! This forces the panel to anchor its view to the bottom-most text,
        # meaning overflowing text gets clipped at the TOP, exactly like a terminal.
        bottom_aligned_logs = Align(text_obj, align="left", vertical="bottom")

        self._layout["lower"].update(
                Panel(bottom_aligned_logs, title="Turn Log", border_style="blue")
                )
        self._live.refresh()

    def render_turn(self, turn: int, drones: Dict[str, Drone]) -> None:
        """Updates the table in place without breaking headless logic."""
        table = self.render_map_info(turn, drones)
        # Update what the Live display is showing
        if self._live:
            # self._live.update(table)
            self._layout["upper"].update(table)
            self._live.refresh()
        else:
            self._console.print(table)

    def render_map_info(self, turn: int, drones: Dict[str, Drone]) -> Table:
        # 1. Get total available terminal height
        term_height = self._console.height
        max_zone_len = max((len(z) for z in self.map_graph.get_zones()), default=10)
        znl = max_zone_len + 1

        # 2. Reserve space for your bottom log panel (e.g., 10 rows)
        # and table headers/borders (e.g., 5 rows)
        reserved_space = 15
        max_table_rows = max(5, term_height - reserved_space)

        # 3. If you have more zones than max_table_rows, slice the list!
        # (Prioritizing zones that currently have drones)
        all_zones = list(self.map_graph.get_zones().values())
        # Sort so zones with drones are at the top, or just take a slice
        active_zones = [z for z in all_zones if any(
            d.current_location == z.name for d in drones.values())]
        inactive_zones = [z for z in all_zones if z not in active_zones]

        # Combine them up to our budget limit
        displayed_zones = (active_zones + inactive_zones)[:max_table_rows]

        table = Table(
            title=f"[bold cyan]Simulation Dashboard — Turn {turn}[/bold cyan]",
            box=box.ROUNDED,
            header_style="bold magenta",
            border_style="bright_blue",
            expand=True
        )
        table.add_column(
                "Zone", no_wrap=True, style="bold white", justify="left", min_width=znl)
        table.add_column("Type", no_wrap=True, justify="center", min_width=4)
        table.add_column("Neighbors", no_wrap=True, style="dim", justify="left", ratio=1)
        table.add_column("Max", no_wrap=True, justify="center", min_width=3)
        table.add_column("Drones", justify="left", width=20, no_wrap=True)
        
        # logic to loop through map._adj_list and add rows...
        for node in self.map_graph.get_zones().values():
        # for node in displayed_zones:
            neighbor_strings = []
            neighbors = {(c.end_point2 if c.end_point1 == node.name else c.end_point1):
                    c.max_link_capacity
                    for c in self.map_graph._adj_list[node.name]}

            # Format it cleanly, e.g., "tunnel (cap: 1)" or just "(1)"
            for name, cap in neighbors.items():
                if cap > 1:
                    neighbor_strings.append(
                        f"{name}[bold yellow]({cap})[/bold yellow]")
                else:
                    neighbor_strings.append(
                        f"{name}[gray53](1)[/gray53]")

            # Color-code zone types dynamically
            z_type = node.metadata.zone_type
            type_string = z_type[:1].upper()
            if z_type == "restricted":
                type_line = f"[bold red]{type_string}[/bold red]"
            elif z_type == f"priority":
                type_line = f"[bold green]{type_string}[/bold green]"
            elif z_type == f"blocked":
                type_line = f"[bold dim red]{type_string}[/bold dim red]"
            else:
                type_line = f"[blue]{type_string}[/blue]"

            # Find drones in this zone
            zone_drones = [d.id for d in drones.values() if d.current_location == node.name]
            drones_count = len(zone_drones)
            limit = 5
            if drones_count <= limit:
                drones_str = ", ".join(
                    f"[bold yellow]{d}[/bold yellow]" for d in zone_drones[:limit])
            else:
                drones_str = ", ".join(
                    f"[bold yellow]{d}[/bold yellow]" for d in zone_drones[:limit - 1])
                drones_str += f"[yellow] (+{drones_count})[/yellow]"

            table.add_row(
                node.name,
                type_line,
                ", ".join(neighbor_strings),
                str(node.metadata.max_drones),
                drones_str
            )

        return table
"""            table.add_row(
                    node.name,
                    node.metadata.zone_type,
                    ",".join(neighbors),
                    str(node.metadata.max_drones),
                    ",".join([d.id for d in filter(
                        lambda d: d.current_location == node.name,drones.values())])
                    )"""
