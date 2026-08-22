from models import Map
from parser import Parser
import sys


if __name__ == "__main__":
    my_map = Map()
    parser = Parser(my_map)
    try:
        parser.parse_file("../maps/easy/02_simple_fork.txt")
    except OSError as e:
        print(e)
        sys.exit()
    my_map.initialize_graph()
    print(my_map.to_json())
