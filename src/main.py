from models import Map
from parser import Parser


if __name__ == "__main__":
    my_map = Map()
    parser = Parser(my_map)
    parser.parse_file("maps/easy1.txt")
    my_map.initialize_graph()
    print(my_map.to_json())
