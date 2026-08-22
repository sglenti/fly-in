from models import Map
from parser import Parser
import sys


if __name__ == "__main__":
    sim_map = Map()
    parser = Parser(sim_map)
    try:
        parser.parse_file(sys.argv[1])
    except OSError as e:
        print(e)
        sys.exit()
    sim_map.initialize_graph()
    print(sim_map.to_json())
    sim_map.print_topology()
