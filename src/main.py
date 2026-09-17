import sys
import os
from src.models import Map
from src.parser import Parser
from src.simulation import SimulationEngine
from src.view import ConsoleRenderer
from src.view import WindowRenderer
import pygame
import time
from rich.console import Console
from rich.markup import escape
from typing import List
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"


class Application:
    def __init__(
            self,
            map_file: str,
            interactive: bool = False,
            heuristics: bool = False
            ) -> None:
        self.map_file = map_file
        self.map_graph = Map()
        self.engine = SimulationEngine(self.map_graph)
        self.renderer = ConsoleRenderer(self.map_graph)
        self.error_console = Console(stderr=True)
        self.interactive = interactive
        self.heuristics = heuristics

    def run(self) -> None:
        # 1. Parse and Build:
        parser = Parser(self.map_graph, self.engine)
        try:
            parser.parse_file(self.map_file)
            self.map_graph.initialize_graph()
            self.engine.check_connectivity()
        except Exception as e:
            self.error_console.print(escape(f"Map File Error:\n {e}"))
            sys.exit()

        # 2. Gentlemen, starts engines:
        self.engine.calculate_paths(self.heuristics)
        clock = pygame.time.Clock()

        # 3. Prepare views:
        console_view = ConsoleRenderer(self.map_graph)
        window_view = WindowRenderer(self.map_graph, 80)
        pygame.display.set_caption(
                f"Fly-in - {os.path.basename(self.map_file)}")
        console_view.start_session()

        # 4. Execute simulation:
        window_view.draw_animated_turn(self.engine.get_drones(), clock)
        console_view.render_turn(0, self.engine.get_drones())
        time.sleep(1)
        self.engine.start()
        while self.engine.is_running():
            paused = self.interactive
            while paused:
                clock.tick(6)
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_n:
                            paused = False
                        if event.key == pygame.K_q:
                            paused = False
                            self.engine.stop()
                            pygame.quit()
            if not self.engine.is_running():
                break
            try:
                self.engine.process_turn()
            except Exception as e:
                console_view.end_session()
                pygame.quit()
                self.engine.stop()
                self.error_console.print(f"[bold red]Error:[/bold red] {e}")
                sys.exit()
            occupancy_map = self.engine.calculate_all_occupancies()
            window_view.draw_animated_turn(
                    self.engine.get_drones(), clock)
            console_view.render_turn(
                    self.engine.get_turn(), self.engine.get_drones())
            console_view.print_line(
                    self.engine.get_turn(), self.engine.get_turn_moves())

            if (occupancy_map[self.map_graph.get_end()] ==
                    self.engine.get_nb_drones()):
                self.engine.stop()
            time.sleep(1.5)

        # 5. Closing
        while pygame.get_init() and pygame.display.get_surface() is not None:
            window_view.draw_static_map()
            clock.tick(6)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        pygame.quit()
        console_view.end_session()


def main(args: List[str] = sys.argv[1:]) -> None:
    interactive = False
    heuristics = False
    if "--interactive" in args:
        interactive = True
        args.remove("--interactive")
    if "--heuristics" in args:
        heuristics = True
        args.remove("--heuristics")
    if len(args) != 1:
        print("Usage: python3 -m src [option] <map_file>"
              "\n Options:"
              "\n --interactive     step-by-step mode"
              "\n --heuristics      enable A* heuristics")
        sys.exit(1)
    map_file: str = args[0]
    # app = Application(map_file, interactive, heuristics)
    app = Application(map_file, interactive, heuristics)
    app.run()


if __name__ == "__main__":
    main()
