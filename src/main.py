from models import Map
from parser import Parser
from simulation import SimulationEngine
from view import ConsoleRenderer
from view import WindowRenderer
import sys
import pygame
import time
from rich import print as rprint


class Application:
    def __init__(self, map_file: str) -> None:
        self.map_file = map_file
        self.map_graph = Map()
        self.engine = SimulationEngine(self.map_graph)
        self.renderer = ConsoleRenderer(self.map_graph)

    def run(self) -> None:
        # 1. Parse and Build:
        parser = Parser(self.map_graph, self.engine)
        try:
            parser.parse_file(self.map_file)
        except OSError as e:
            print(e)
            sys.exit()
        self.map_graph.initialize_graph()
    #    print(sim_map.to_json())
    #    print(sim_engine._drones)
    #    sim_map.print_topology()

        # 2. Gentlemen, starts engines:
        self.engine.calculate_paths()

        # 3. Prepare views:
        console_view = ConsoleRenderer(self.map_graph)
        window_view = WindowRenderer(self.map_graph)

        # 4. Execute simulation:
        self.engine.start()
    #    console_view.start_session()
        console_view.render_turn(0, self.engine.get_drones())
    #    console_view.render_map_info(self.engine.get_drones())
    #    clock = pygame.time.Clock()
        while self.engine.is_running():
    #    for turn in range(8, 1):
            self.engine.process_turn()
            window_view.draw()
    #        clock.tick(60)
            occupancy_map = self.engine.calculate_all_occupancies()
            print(f"Turn {self.engine.get_turn()}:", occupancy_map)
            # console_view.render_turn(self.engine.get_turn(), self.engine.get_drones())

            if (occupancy_map[self.map_graph.get_end()] ==
                    self.engine.get_nb_drones()):
                self.engine.stop()
            time.sleep(0.5)

        rprint(self.map_graph.get_adj_list())
        rprint(self.engine.get_link_res())
        # 5. Closing
        while pygame.get_init() and pygame.display.get_surface() is not None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
        console_view.end_session()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 -m src.main <map_file>")
        sys.exit(1)
        
    app = Application(sys.argv[1])
    app.run()


if __name__ == "__main__":
    main()
