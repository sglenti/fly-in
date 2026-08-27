from models import Map
from parser import Parser
from simulation import SimulationEngine
from view import ConsoleRenderer
from view import WindowRenderer
import sys
import pygame
from rich import print as rprint


if __name__ == "__main__":
    sim_map = Map()
    sim_engine = SimulationEngine(sim_map)
    parser = Parser(sim_map, sim_engine)
    try:
        parser.parse_file(sys.argv[1])
    except OSError as e:
        print(e)
        sys.exit()
    sim_map.initialize_graph()
    print(sim_map.to_json())
    print(sim_engine._drones)
    sim_map.print_topology()
    console_view = ConsoleRenderer(sim_map)
#    window = WindowRenderer(sim_map)
    sim_engine.start()
#    clock = pygame.time.Clock()
#    while sim_engine.is_running():
#        for event in pygame.event.get():
#            if event.type == pygame.QUIT:
#                sim_engine.stop()
#        sim_engine.process_turn()
        # window.draw()
#        clock.tick(60)
    occupancy_map = sim_engine.calculate_all_occupancies()
    rprint(sim_map._adj_list)
    console_view.render_map_info(sim_engine._drones)
    sim_engine.process_turn()
