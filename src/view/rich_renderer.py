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
        self._live: Live
        self._layout = Layout()
        self.log_history: List[str] = []
        self.moves_history: List[str] = []

    def start_session(self) -> None:
        """Starts the live terminal display session."""
        upper_size = min(
                self._console.height - 15, len(self.map_graph.get_zones()) + 5)
        self._layout.split_column(
            Layout(name="upper", size=upper_size),
            Layout(name="lower")
        )
        # Initial empty table and layout:
        table = Table()
        self._layout["upper"].update(table)
        self._layout["lower"].update(
                Panel("", title="Turn Log", border_style="blue",
                      ))
        self._live = Live(
                self._layout,
                console=self._console,
                transient=True,
                auto_refresh=False)
        self._live.start()

    def end_session(self) -> None:
        """Stops the live terminal display session."""
        if self._live:
            self._live.stop()

    def print_line(self, turn: int, moves: List[str]) -> None:
        self.moves_history.append(' '.join(moves))
        move_log_string = (f"[yellow]Turn {turn}:[/yellow] "
                           f"{' '.join(moves)} "
                           f"[cyan]({len(moves)} moves)[/cyan]")
        self.log_history.append(move_log_string)
        # Last 50 lines
        recent_logs = "\n".join(reversed(
            self.log_history[-50:-1] + [f"[bold]{move_log_string}[/bold]"]))

        aligned_logs = Align(recent_logs, align="left", vertical="top")
        # Update log panel content:
        self._layout["lower"].update(
                Panel(aligned_logs, title="Turn Log", border_style="blue",
                      )
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
        max_zone_len = max(
                (len(z) for z in self.map_graph.get_zones()), default=10)
        znl = max_zone_len + 1  # Zone lenght
        tpl = 4 if w < 100 else 10  # Type lenght
        mxl = 3  # Max capacity length
        # Drones length:
        nb_d = len(drones)
        d_limit = 3 if w < 100 else 5  # max number of drones shown
        max_drone_len = max((len(d) for d in drones), default=3) + 2
        drl = min(max_drone_len * d_limit, max(10, nb_d * max_drone_len)) - 1

        # 2. Reserve space for bottom log panel
        # and table headers/borders (5 rows)
        reserved_space = 15
        max_table_rows = max(5, h - reserved_space) - 5

        # 3. If we have more zones than max_table_rows, slice the list!
        # (Following drones moving front)
        all_zones = list(self.map_graph.get_zones().values())
        active_zones = [z for z in all_zones if (any(
            ((d.path and d.path[0][0] == z.name)
                or d.current_location == z.name)
            for d in drones.values()))]
        # If we cannot fit everything, follow drones
        if len(all_zones) > max_table_rows:
            last_index = max(
                    max_table_rows - 1, all_zones.index(active_zones[-1]))
            displayed_zones = all_zones[
                    last_index + 1 - max_table_rows:last_index + 1]
        else:
            displayed_zones = all_zones

        # Build table:
        table = Table(
            title=f"[bold cyan]Simulation Dashboard — Turn {turn}[/bold cyan]",
            box=box.ROUNDED,
            header_style="bold magenta",
            border_style="bright_blue",
            expand=True
        )
        table.add_column(
            "Zone", no_wrap=True, style="bold white",
            justify="left", min_width=znl)
        table.add_column("Type", no_wrap=True, justify="center", min_width=tpl)
        table.add_column(
            "Neighbors", no_wrap=True, style="dim", justify="left", ratio=1)
        table.add_column("Max", no_wrap=True, justify="center", min_width=mxl)
        table.add_column("Drones", justify="left", width=drl, no_wrap=True)

        # Fill table rows:
        for node in displayed_zones:
            # for node in displayed_zones:
            neighbor_strings = []
            neighbors = {
                (c.end_point2 if c.end_point1 == node.name else c.end_point1):
                c.max_link_capacity
                for c in self.map_graph.get_adj_list().get(node.name, [])}

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
            elif z_type == "priority":
                type_line = f"[bold green]{type_string}[/bold green]"
            elif z_type == "blocked":
                type_line = f"[bold grey53 ]{type_string}[/bold grey53]"
            else:
                type_line = f"[blue]{type_string}[/blue]"

            # Find drones in this zone
            zone_drones = [d.id for d in drones.values()
                           if d.current_location == node.name]
            # Find Drones in transit
            transit_drones = [
                    d.id for d in drones.values() if
                    (d.status == "in_transit" and d.path
                        and d.path[0][0] == node.name)
                    and d.current_location is None]
            drones_count = len(zone_drones) + len(transit_drones)
            drones_list = (
                [f"[bold yellow]{d}[/bold yellow]" for d in zone_drones] +
                [f"[bold grey53]{d}[/bold grey53]" for d in transit_drones])
            if drones_count <= d_limit:
                drones_str = ", ".join(drones_list)
            else:
                drones_str = ", ".join(drones_list[:d_limit - 1])
                excess_drones = drones_count - (d_limit - 1)
                drones_str += f"[yellow] (+{excess_drones})[/yellow]"

            table.add_row(
                node.name,
                type_line,
                ", ".join(neighbor_strings),
                str(node.metadata.max_drones),
                drones_str
            )

        return table

    def dump_moves(self) -> None:
        for line in self.moves_history:
            print(line)

    def print_stats(self) -> None:
        turns = len(self.moves_history)
        if turns == 0:
            return
        moves_per_drone: Dict[str, int] = {}
        drone_delivery: Dict[str, int] = {}
        total_cost: int = 0
        for t, line in enumerate(self.moves_history, 1):
            drones = line.split()
            for d in drones:
                d = d.split("-")[0]
                moves_per_drone[d] = moves_per_drone.get(d, 0) + 1
                drone_delivery[d] = t
            total_cost += len(line.split())
        avg_moves = (sum(moves_per_drone.values()) / len(moves_per_drone))
        avg_turns = (sum(drone_delivery.values()) / len(moves_per_drone))
        peak = max(len(l.split()) for l in self.moves_history)
        stats: str = (
            f"[bold cyan]Avg moves p/ drone:[/bold cyan] [green]{avg_moves:.2f}[/green]\n"
            f"[bold cyan]Avg turns p/ drone:[/bold cyan] [green]{avg_turns:.2f}[/green]\n"
            f"[bold cyan]Peak concurrency:[/bold cyan]   [yellow]{peak}[/yellow]\n"
            f"[bold cyan]Total cost:[/bold cyan]         [magenta]{total_cost}[/magenta]\n"
        )
        aligned_stats = Align(stats, align="left", vertical="top")
        self._layout["lower"].update(
                Panel(
                    aligned_stats,
                    title="Final Metrics",
                    border_style="blue",
                      )
                )
        self._live.refresh()
