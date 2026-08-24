import pygame
from src.models import Map

class WindowRenderer:
    def __init__(self, map_graph: Map, scale: int = 100, offset: int = 100) -> None:
        pygame.init()
        self.map_graph = map_graph
        self.scale = scale
        self.offset = offset
        # Simple window sizing based on your map bounds would be an improvement later
        self.screen = pygame.display.set_mode((2000, 600))
        self.font = pygame.font.SysFont("Arial", 10)

    def _to_pixels(self, x: int, y: int) -> tuple[int, int]:
        """Convert logical grid coordinates to pixel coordinates."""
        return (x * self.scale + self.offset / 4, y * self.scale + self.offset)

    def draw(self) -> None:
        self.screen.fill((30, 30, 30))  # Dark gray background

        # 1. Draw Connections (Edges)
        for conn in self.map_graph._connections:
            # We need to look up the actual zones to get their coordinates
            z1 = self.map_graph._zones[conn.source_name]
            z2 = self.map_graph._zones[conn.target_name]
            pygame.draw.line(self.screen, (200, 200, 200), 
                             self._to_pixels(z1.x, z1.y), 
                             self._to_pixels(z2.x, z2.y), 2)

        # 2. Draw Zones (Nodes)
        for zone in self.map_graph._zones.values():
            pos = self._to_pixels(zone.x, zone.y)
            # Draw circle
            pygame.draw.circle(self.screen, (0, 128, 255), pos, 15)
            # Draw label
            text = self.font.render(zone.name, True, (255, 255, 255))
            self.screen.blit(text, (pos[0] - (len(zone.name) / 2) * 5, pos[1] + 20))

        pygame.display.flip()
