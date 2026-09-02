import pygame
from rich.color import Color
from src.models import Map, Drone
from typing import Optional, Dict


def get_rgb(color_name: Optional[str]) -> tuple[int, int, int]:
    if not color_name:
        return (128, 128, 128)
        
    clean_name = color_name.lower().strip()
    
    # Try the raw name first (e.g. "red", "cyan", or a hex code like "#FFA500")
    # Then try appending "1" if it fails (like "orange" -> "orange1")
    for variant in [clean_name, f"{clean_name}1"]:
        try:
            return Color.parse(variant).get_truecolor()
        except Exception:
            continue
            
    # Ultimate fallback if neither works
    return (128, 128, 128)


class WindowRenderer:
    def __init__(self, map_graph: Map, scale: int = 100) -> None:
        pygame.init()
        self.map_graph = map_graph
        self.scale = scale
        self.x_max: int = max([n.x for n in self.map_graph.get_zones().values()])
        self.x_min: int = min([n.x for n in self.map_graph.get_zones().values()])
        self.y_max: int = max([n.y for n in self.map_graph.get_zones().values()])
        self.y_min: int = min([n.y for n in self.map_graph.get_zones().values()])
        self.x_offset = scale - self.x_min * scale
        self.y_offset = scale - self.y_min * scale
        # Simple window sizing based on your map bounds would be an improvement later
        self.screen = pygame.display.set_mode(self._set_size())
        self.font = pygame.font.SysFont("Arial", 10)

    def _set_size(self) -> int:
        return ((self.x_max - self.x_min + 2) * self.scale,
                (self.y_max - self.y_min + 2) * self.scale)

    def _to_pixels(self, x: int, y: int) -> tuple[int, int]:
        """Convert logical grid coordinates to pixel coordinates."""
        return (x * self.scale + self.x_offset, y * self.scale + self.y_offset)

    def draw(self, drones: Dict[str, Drone]) -> None:
        self.screen.fill(get_rgb("gray15"))  # Dark gray background

        # 1. Draw Connections (Edges)
        for conn in self.map_graph.get_conn_list():
            # We need to look up the actual zones to get their coordinates
            z1 = self.map_graph.get_zones()[conn.end_point1]
            z2 = self.map_graph.get_zones()[conn.end_point2]
            pygame.draw.line(self.screen, (get_rgb("white")), 
                             self._to_pixels(z1.x, z1.y), 
                             self._to_pixels(z2.x, z2.y), 2)

        # 2. Draw Zones (Nodes)
        for zone in self.map_graph.get_zones().values():
            pos = self._to_pixels(zone.x, zone.y)
            # Draw circle
            pygame.draw.circle(self.screen, get_rgb(zone.metadata.color), pos, 20)
            # Draw label
            # 1. Prepare your colors
            text_color = (255, 255, 255)
            shadow_color = (0, 0, 0) # Black shadow

            # 2. Render Shadow
            shadow_surf = self.font.render(zone.name, True, shadow_color)
            self.screen.blit(
                    shadow_surf, (pos[0] - (len(zone.name) / 2) * 5 + 1, pos[1] + 20 + 1))

            # 3. Render Original Text
            text_surf = self.font.render(zone.name, True, text_color)
            self.screen.blit(text_surf, (pos[0] - (len(zone.name) / 2) * 5, pos[1] + 20))


        # 3. Draw Drones
        for drone in drones.values():
            location = self.map_graph.get_zones().get(drone.current_location, None)
            if location:
                pos = self._to_pixels(location.x, location.y)
                pygame.draw.circle(self.screen, get_rgb("black"), pos, 10)
                text_surf = self.font.render(drone.id, True, text_color)
                self.screen.blit(text_surf, (pos[0] - (len(drone.id) / 2) * 5, pos[1] - 5))

        pygame.display.flip()
