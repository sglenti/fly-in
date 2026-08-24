from models import Map
from parser import Parser
from view import ConsoleRenderer
from view import WindowRenderer
import sys
import pygame


if __name__ == "__main__":
    sim_map = Map()
    parser = Parser(sim_map)
    try:
        parser.parse_file(sys.argv[1])
    except OSError as e:
        print(e)
        sys.exit()
    sim_map.initialize_graph()
#    sim_map.print_topology()
    print(sim_map.to_json())
    view = ConsoleRenderer(sim_map)
    window = WindowRenderer(sim_map, 80, 200)
    running = True
    clock = pygame.time.Clock()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        window.draw()
        clock.tick(60)
    view.render_map_info()
