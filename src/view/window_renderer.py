import pygame
import math
from rich.color import Color
from src.models import Map, Drone, DroneStatus
from typing import Optional, Dict, Tuple


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
        self.curr_drones_pos: Dict[str, str] = {} # drone_id -> zone_name
        self.prev_drones_pos: Dict[str, str] = {} # drone_id -> zone_name

    def _set_size(self) -> int:
        return ((self.x_max - self.x_min + 2) * self.scale,
                (self.y_max - self.y_min + 2) * self.scale)

    def _to_pixels(self, x: int, y: int) -> tuple[int, int]:
        """Convert logical grid coordinates to pixel coordinates."""
        return (x * self.scale + self.x_offset, y * self.scale + self.y_offset)

    def _lerp(self, p1: tuple[float, float], p2: tuple[float, float], t: float
            )-> tuple[float, float]:
        x1, y1 = p1
        x2, y2 = p2
        return (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)

    def _draw_abstract_drone(self, center: Tuple[float, float], drone_id: str, size=16):
        cx, cy = center
        color = get_rgb("black")
        surface = self.screen
        
        # 1. Draw the central square body
        # We use a rect centered at (cx, cy)
        body_rect = pygame.Rect(0, 0, size, size)
        body_rect.center = (cx, cy)
        pygame.draw.rect(surface, color, body_rect)
        
        # Optional: Draw a dark outline on the body so it pops
        # pygame.draw.rect(surface, get_rgb("silver"), body_rect, 1)

        # 2. Draw the 4 rotor circles at the corners
        # Calculate offset distance from center to corners
        offset = size // 2
        rotor_radius = 4
        rotor_color = get_rgb("black") # Silver/White rotors
        
        # Top-Left, Top-Right, Bottom-Left, Bottom-Right
        corners = [
            (cx - offset, cy - offset),
            (cx + offset, cy - offset),
            (cx - offset, cy + offset),
            (cx + offset, cy + offset)
        ]
        
        for corner in corners:
            pygame.draw.circle(surface, rotor_color, corner, rotor_radius)
            # Optional outline for the rotors
            pygame.draw.circle(surface, get_rgb("grey15"), corner, rotor_radius, 1)
        
        # 3. Drone label
        text_surf = self.font.render(drone_id, True, get_rgb("white"))
        text_rect = text_surf.get_rect()
        text_rect.center = (center[0], center[1])
        self.screen.blit(text_surf, text_rect)

    def _get_dock_position(
            self,
            center: tuple[float, float],
            index: int,
            total_drones: int,
            radius: float = 20.0
            ) -> tuple[float, float]:
        if total_drones <= 1:
            return center
            
        cx, cy = center
        # Calculate angle for this specific drone
        angle = (2 * math.pi * index) / total_drones
        
        # Offset from center
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        return (x, y)

    def draw_static_map(self) -> None:
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

        """
        # 3. Draw Drones
        for drone in drones.values():
            location = self.map_graph.get_zones().get(drone.current_location, None)
            if location:
                pos = self._to_pixels(location.x, location.y)
                self._draw_abstract_drone(pos, drone.id)
                rect = (pos[0] - 10, pos[1] - 10, 20, 20)
                pygame.draw.rect(self.screen, get_rgb("black"), rect)
                text_surf = self.font.render(drone.id, True, text_color)
                text_rect = text_surf.get_rect()
                text_rect.center = (pos[0], pos[1])
                self.screen.blit(text_surf, text_rect)
        """
        pygame.display.flip()

    def draw_animated_turn(
            self,
            drones: Dict[str, Drone],
            clock: pygame.time.Clock) -> None:
        # 1. Categorize drones ONCE at the start of the turn animation
        docked_groups: Dict[str, list[str]] = {}
        moving_drones = {}
        in_transit = {}

        for d_id, drone in drones.items():
            if drone.status == DroneStatus.WAITING or drone.status == DroneStatus.DELIVERED:
                loc = drone.current_location
                if loc not in docked_groups:
                    docked_groups[loc] = []
                docked_groups[loc].append(d_id)
            elif drone.status == DroneStatus.IN_TRANSIT:
                in_transit[d_id] = drone
            else:
                moving_drones[d_id] = drone
        
        # 2. Update positions: Old becomes current, Current becomes new targets
        self.prev_drones_pos = self.curr_drones_pos.copy()
        self.curr_drones_pos = {d_id: d.current_location for d_id,
                d in drones.items()}

        # 3. Animation sub-loop (e.g., 30 frames for the turn transition)
        frames = 30
        for frame in range(frames + 1):
            t = frame / frames  # Progress from 0.0 (start of turn) to 1.0 (end of turn)
            
            # Handle window close events during animation so it doesn't feel frozen
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
            # Clear screen and draw static map (zones and connections)
            self.draw_static_map()
            
            # 4. Draw drones at interpolated positions
            for d_id, drone in moving_drones.items():
                start_zone_name = self.prev_drones_pos.get(
                        d_id, drone.current_location)
                target_zone_name = drone.current_location
                
                # Get pixel coordinates for start and target zones
                z_start = self.map_graph.get_zones().get(start_zone_name)
                z_target = self.map_graph.get_zones().get(target_zone_name)

                if z_start and z_target:
                    p1 = self._to_pixels(z_start.x, z_start.y)
                    p2 = self._to_pixels(z_target.x, z_target.y)

                    # Calculate smooth position using Lerp!
                    current_pixel_pos = self._lerp(p1, p2, t)

                    # Draw the drone at this interpolated pixel position
                    self._draw_abstract_drone(current_pixel_pos, drone.id)

            # 5. Draw drones in transit:
            for d_id, drone in in_transit.items():
                if not drone.current_location:
                    self.curr_drones_pos[d_id] = self.prev_drones_pos[d_id]
                    start_zone_name = self.prev_drones_pos.get(d_id)
                    target_zone_name = drone.path[0][0]
                else:
                    start_zone_name = self.prev_drones_pos.get(d_id)
                    target_zone_name = drone.current_location

                # Get pixel coordinates for start and target zones
                z_start = self.map_graph.get_zones().get(start_zone_name)
                z_target = self.map_graph.get_zones().get(target_zone_name)

                if z_start and z_target:
                    p1 = self._to_pixels(z_start.x, z_start.y)
                    p2 = self._to_pixels(z_target.x, z_target.y)
                    p_middle = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)

                    # Calculate smooth position using Lerp!
                    if not drone.current_location:
                        current_pixel_pos = self._lerp(p1, p_middle, t)
                    else:
                        current_pixel_pos = self._lerp(p_middle, p2, t)

                    # Draw the drone at this interpolated pixel position
                    self._draw_abstract_drone(current_pixel_pos, drone.id)

            # 6. Draw docked drones
            for name, dock in docked_groups.items():
                zone = self.map_graph.get_zones().get(name)
                if zone:
                    for d_idx, drone in enumerate(dock, 1):
                        docked_pos = self._get_dock_position(
                                self._to_pixels(zone.x, zone.y), d_idx, len(dock))
                        self._draw_abstract_drone(docked_pos, drone)
            pygame.display.flip()
            clock.tick(60) # Keep it locked at 60 FPS for butter-smooth motion

        for d_id, drone in in_transit.items():
            if drone.current_location:
                if drone.current_location not in docked_groups:
                    docked_groups[drone.current_location] = []
                docked_groups[drone.current_location].append(d_id)
        
        # 4: Dock drones after arrival:
        self.draw_static_map()
        for d in moving_drones.values():
            if d.current_location not in docked_groups:
                docked_groups[d.current_location] = []
            docked_groups[d.current_location].append(d.id)
        for name, dock in docked_groups.items():
            zone = self.map_graph.get_zones().get(name)
            if zone:
                for d_idx, drone in enumerate(dock, 1):
                    if drone in in_transit:
                        in_transit.pop(drone)                        
                    docked_pos = self._get_dock_position(
                            self._to_pixels(zone.x, zone.y), d_idx, len(dock))
                    self._draw_abstract_drone(docked_pos, drone)
        for d_id, drone in in_transit.items():
            start_zone_name = self.prev_drones_pos.get(d_id)
            target_zone_name = drone.path[0][0]
            z_start = self.map_graph.get_zones().get(start_zone_name)
            z_target = self.map_graph.get_zones().get(target_zone_name)
            
            if z_start and z_target:
                p1 = self._to_pixels(z_start.x, z_start.y)
                p2 = self._to_pixels(z_target.x, z_target.y)
                p_middle = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
                self._draw_abstract_drone(p_middle, drone.id)

        pygame.display.flip()
