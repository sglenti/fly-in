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
    
    def start_session(self) -> None:
        """Starts the live terminal display session."""
        self._layout.split_column(
            Layout(name="upper", size=(len(self.map_graph.get_zones()) + 5)),
            Layout(name="lower")
        )
        # Initial empty table:
        table = Table()
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
        move_log_string = f"Turn {turn}: {' '.join(moves)}"
        self.log_history.append(move_log_string)
        # Last 50 lines
        recent_logs = "\n".join(self.log_history[-50:]) 
        # Wrap in Text
        text_obj = Text(recent_logs)
    
        # Align to bottom! This forces the panel to anchor its view to the bottom-most text,
        # meaning overflowing text gets clipped at the TOP, like a terminal.
        bottom_aligned_logs = Align(text_obj, align="left", vertical="bottom")
        # Update log panel content:
        self._layout["lower"].update(
                Panel(bottom_aligned_logs, title="Turn Log", border_style="blue")
                )
        self._live.refresh()

    def render_turn(self, turn: int, drones: Dict[str, Drone]) -> None:
        """Updates the table in place without breaking headless logic."""
        table = self.render_map_info(turn, drones)
        # Update what the Live display is showing
        if self._live:
            self._layout["upper"].update(table)
            self._live.refresh()
        else:
            self._console.print(table)

    def render_map_info(self, turn: int, drones: Dict[str, Drone]) -> Table:
        # 1. Get total available terminal dimensions:
        h = self._console.height
        w = self._console.width
        # Define columns width:
        max_zone_len = max((len(z) for z in self.map_graph.get_zones()), default=10)
        znl = max_zone_len + 1  # Zone lenght
        tpl = 4 if w < 100 else 10  # Type lenght
        mxl = 3  # Max capacity length
        # Drones length:
        nb_d = len(drones) 
        d_limit = 5  # max number of drones shown
        max_drone_len = max((len(d) for d in drones), default=3) + 2
        drl = min(max_drone_len * d_limit, max(10, nb_d * max_drone_len))

        # 2. Reserve space for your bottom log panel (e.g., 10 rows)
        # and table headers/borders (e.g., 5 rows)
        reserved_space = 15
        max_table_rows = max(5, h - reserved_space)

        """
        # 3. If you have more zones than max_table_rows, slice the list!
        # (Prioritizing zones that currently have drones)
        all_zones = list(self.map_graph.get_zones().values())
        # Sort so zones with drones are at the top, or just take a slice
        active_zones = [z for z in all_zones if any(
            d.current_location == z.name for d in drones.values())]
        inactive_zones = [z for z in all_zones if z not in active_zones]
        # Combine them up to our budget limit
        displayed_zones = (active_zones + inactive_zones)[:max_table_rows]
        """

        # Build table:
        table = Table(
            title=f"[bold cyan]Simulation Dashboard — Turn {turn}[/bold cyan]",
            box=box.ROUNDED,
            header_style="bold magenta",
            border_style="bright_blue",
            expand=True
        )
        table.add_column(
                "Zone", no_wrap=True, style="bold white", justify="left", min_width=znl)
        table.add_column("Type", no_wrap=True, justify="center", min_width=tpl)
        table.add_column("Neighbors", no_wrap=True, style="dim", justify="left", ratio=1)
        table.add_column("Max", no_wrap=True, justify="center", min_width=mxl)
        table.add_column("Drones", justify="left", width=drl, no_wrap=True)
        
        # logic to loop through map._adj_list and add rows...
        for node in self.map_graph.get_zones().values():
            # for node in displayed_zones:
            neighbor_strings = []
            neighbors = {(c.end_point2 if c.end_point1 == node.name else c.end_point1):
                    c.max_link_capacity
                    for c in self.map_graph._adj_list[node.name]}

            # Link capacity
            for name, cap in neighbors.items():
                if cap > 1:
                    neighbor_strings.append(
                        f"{name}[bold yellow]({cap})[/bold yellow]")
                else:
                    neighbor_strings.append(
                        f"{name}[gray53](1)[/gray53]")

            # Color-code zone types dynamically
            z_type = node.metadata.zone_type
            # if narrow cosole, show type first letter only
            type_string = z_type[:1].upper() if tpl == 4 else z_type
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
            if drones_count <= d_limit:
                drones_str = ", ".join(
                    f"[bold yellow]{d}[/bold yellow]" for d in zone_drones)
            else:
                drones_str = ", ".join(
                    f"[bold yellow]{d}[/bold yellow]" for d in zone_drones[:d_limit - 1])
                drones_str += f"[yellow] (+{drones_count - (d_limit - 1)})[/yellow]"

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
