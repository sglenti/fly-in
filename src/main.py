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
        clock = pygame.time.Clock()

        # 3. Prepare views:
        console_view = ConsoleRenderer(self.map_graph)
        # window_view = WindowRenderer(self.map_graph, 75)
        console_view.start_session()

        # 4. Execute simulation:
        # window_view.draw_animated_turn(self.engine.get_drones(), clock)
        time.sleep(1.5)
        self.engine.start()
        console_view.render_turn(0, self.engine.get_drones())
        while self.engine.is_running():
            self.engine.process_turn()
            occupancy_map = self.engine.calculate_all_occupancies()
            # window_view.draw_animated_turn(self.engine.get_drones(), clock)
            console_view.render_turn(self.engine.get_turn(), self.engine.get_drones())
            console_view.print_line(self.engine.get_turn(), occupancy_map)

            if (occupancy_map[self.map_graph.get_end()] ==
                    self.engine.get_nb_drones()):
                self.engine.stop()
            time.sleep(1.5)

        # rprint(self.map_graph.get_adj_list())
        # rprint(self.engine.get_link_res())

        # 5. Closing
        while pygame.get_init() and pygame.display.get_surface() is not None:
            # window_view.draw_static_map()
            clock.tick(6)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
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
