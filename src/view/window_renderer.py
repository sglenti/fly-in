"""Window-based rendering utilities for the fly-in visual simulator."""

import pygame
import pygame.gfxdraw
import math
from src.models import Map, Drone, DroneStatus, Connection
from typing import Optional, Dict, Tuple


def get_rgb(color_name: Optional[str]) -> tuple[int, int, int]:
    """Convert a color name or hex code to an RGB tuple.

    Args:
        color_name: A color name (for example ``'red'``) or a hex code.

    Returns:
        A three-channel RGB tuple. If the color is invalid, a neutral gray value
        is returned.
    """
    if not color_name:
        return (128, 128, 128)

    clean_name = color_name.lower().strip()

    for variant in [clean_name, f"{clean_name}1"]:
        try:
            red, green, blue, alpha = pygame.Color(variant)
            return red, green, blue
        except Exception:
            continue

    return (128, 128, 128)


class WindowRenderer:
    """Render the simulation as an animated Pygame map.

    The renderer converts logical map coordinates into screen coordinates and
    animates drones moving along links.

    Attributes:
        map_graph: Graph describing the simulation topology.
        scale: Pixel scale used to size the map and nodes.
        screen: Pygame display surface.
        font: Font used for zone labels and drone IDs.
    """

    def __init__(self, map_graph: Map, scale: int = 100) -> None:
        """Initialize the window renderer and its display surface.

        Args:
            map_graph: Map used to render the scenario.
            scale: Size of one logical unit in pixels.
        """
        pygame.init()
        self.map_graph = map_graph
        self.scale = scale
        self.x_max: int = max(
                [n.x for n in self.map_graph.get_zones().values()])
        self.x_min: int = min(
                [n.x for n in self.map_graph.get_zones().values()])
        self.y_max: int = max(
                [n.y for n in self.map_graph.get_zones().values()])
        self.y_min: int = min(
                [n.y for n in self.map_graph.get_zones().values()])
        self.x_offset = scale - self.x_min * scale
        self.y_offset = scale - self.y_min * scale
        self.screen = pygame.display.set_mode(self._set_size())
        self.font = pygame.font.SysFont("Arial", max(10, scale // 10))
        self.radious: int = max(20, scale // 5)
        self.curr_drones_pos: Dict[str, str] = {}
        self.prev_drones_pos: Dict[str, str] = {}

    def _set_size(self) -> Tuple[float, float]:
        """Compute the display size from the map bounds.

        Returns:
            Width and height in pixels for the display surface.
        """
        return ((self.x_max - self.x_min + 2) * self.scale,
                (self.y_max - self.y_min + 2) * self.scale)

    def _to_pixels(self, x: int, y: int) -> tuple[int, int]:
        """Convert logical map coordinates into pixel coordinates.

        Args:
            x: Logical x coordinate.
            y: Logical y coordinate.

        Returns:
            Screen-space coordinate pair.
        """
        return (x * self.scale + self.x_offset, y * self.scale + self.y_offset)

    def _lerp(self, p1: tuple[int, int], p2: tuple[int, int], t: float
              ) -> tuple[int, int]:
        """Linearly interpolate between two points.

        Args:
            p1: Starting point.
            p2: Ending point.
            t: Interpolation factor between 0 and 1.

        Returns:
            Interpolated point.
        """
        x1, y1 = p1
        x2, y2 = p2
        return (round(x1 + (x2 - x1) * t), round(y1 + (y2 - y1) * t))

    def _draw_abstract_drone(
            self,
            center: Tuple[int, int],
            drone_id: str,
            size: int = 16) -> None:
        """Draw a drone icon at a given center point.

        Args:
            center: Screen-space center point for the drone sprite.
            drone_id: Identifier shown on the drone icon.
            size: Size of the drone body in pixels.
        """
        cx, cy = center
        color = get_rgb("black")
        surface = self.screen

        body_rect = pygame.Rect(0, 0, size, size)
        body_rect.center = (cx, cy)
        pygame.draw.rect(surface, color, body_rect)

        offset = size // 2
        rotor_radius = 4
        rotor_color = get_rgb("black")
        corners = [
            (cx - offset, cy - offset),
            (cx + offset, cy - offset),
            (cx - offset, cy + offset),
            (cx + offset, cy + offset)
        ]
        for corner in corners:
            pygame.draw.circle(surface, rotor_color, corner, rotor_radius)
            pygame.draw.circle(
                    surface, get_rgb("grey15"), corner, rotor_radius, 1)

        text_surf = self.font.render(drone_id, True, get_rgb("white"))
        text_rect = text_surf.get_rect()
        text_rect.center = (center[0], center[1])
        self.screen.blit(text_surf, text_rect)

    def _get_dock_position(
            self,
            center: tuple[int, int],
            index: int,
            total_drones: int,
            radius: float = 20.0
            ) -> tuple[int, int]:
        """Compute the offset position for a drone parked around a hub.

        Args:
            center: Screen-space center of the hub.
            index: Position index among drones in the same hub.
            total_drones: Total number of drones sharing the hub.
            radius: Distance from the hub center.

        Returns:
            Screen-space position for the drone dock marker.
        """
        if total_drones <= 1:
            return center

        cx, cy = center
        angle = (2 * math.pi * index) / total_drones
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        return (round(x), round(y))

    def draw_static_map(self) -> None:
        """Draw the static topology: zones, labels, and links."""
        self.screen.fill(get_rgb("gray15"))

        for conn in self.map_graph.get_conn_list():
            z1 = self.map_graph.get_zones()[conn.end_point1]
            z2 = self.map_graph.get_zones()[conn.end_point2]
            pygame.draw.line(self.screen, (get_rgb("white")),
                             self._to_pixels(z1.x, z1.y),
                             self._to_pixels(z2.x, z2.y), 2)

        rad = self.radious
        text_color = (255, 255, 255)
        shadow_color = (0, 0, 0)
        for zone in self.map_graph.get_zones().values():
            pos = self._to_pixels(zone.x, zone.y)
            zone_color = get_rgb(zone.metadata.color)
            pygame.gfxdraw.filled_circle(
                self.screen,
                pos[0],
                pos[1],
                rad,
                zone_color
            )
            pygame.gfxdraw.aacircle(
                self.screen,
                pos[0],
                pos[1],
                rad,
                zone_color
            )
            lines = zone.name.replace("_", " ").split(" ", 2)
            lineheight = self.font.get_linesize()
            for nb, line in enumerate(lines):
                line = line[:16]
                shadow_surf = self.font.render(line, True, shadow_color)
                shadow_rect = shadow_surf.get_rect(
                    midtop=(pos[0] + 1, pos[1] + rad + 1 + nb * lineheight + 2)
                )
                self.screen.blit(shadow_surf, shadow_rect)
                text_surf = self.font.render(line, True, text_color)
                text_rect = text_surf.get_rect(
                    midtop=(pos[0], pos[1] + rad + nb * lineheight + 2)
                )
                self.screen.blit(text_surf, text_rect)

    def draw_animated_turn(
            self,
            drones: Dict[str, Drone],
            clock: pygame.time.Clock,
            frames: int = 30) -> None:
        """Animate the movement of drones across one turn.

        Args:
            drones: Mapping of drone ids to current drone state.
            clock: Pygame clock controlling the animation timing.
            frames: Number of frames used to interpolate the movement.
        """
        def adjust_t(conn: Connection) -> float:
            """Stagger parallel drone movements to avoid visual overlap.

            Args:
                conn: Link currently being traversed.

            Returns:
                Adjusted interpolation factor for a drone on the link.
            """
            link_index = parallel_moves[conn]
            parallel_moves[conn] += 1
            delay_factor = link_index * 0.15
            t = max(0.0, min(
                1.0, (base_t - delay_factor) / (1.0 - delay_factor)))
            return t

        docked_groups: Dict[str, list[str]] = {}
        moving_drones: Dict[str, Drone] = {}
        in_transit: Dict[str, Drone] = {}
        parallel_moves: Dict[Connection, int] = {}

        for d_id, drone in drones.items():
            loc = drone.current_location
            if loc and (drone.status == DroneStatus.WAITING or
                        drone.status == DroneStatus.DELIVERED):
                if loc not in docked_groups:
                    docked_groups[loc] = []
                docked_groups[loc].append(d_id)
            elif drone.status == DroneStatus.IN_TRANSIT:
                in_transit[d_id] = drone
            else:
                moving_drones[d_id] = drone

        self.prev_drones_pos = self.curr_drones_pos.copy()
        self.curr_drones_pos = {d_id: d.current_location for d_id,
                                d in drones.items() if d.current_location}

        for frame in range(frames + 1):
            base_t = frame / frames
            for c in self.map_graph.get_conn_list():
                if c.max_link_capacity > 1:
                    parallel_moves[c] = 0

            self.draw_static_map()

            for d_id, drone in moving_drones.items():
                start_zone_name = self.prev_drones_pos.get(
                        d_id, drone.current_location)
                target_zone_name = drone.current_location

                if not start_zone_name or not target_zone_name:
                    continue

                conn = self.map_graph.get_connection(
                        start_zone_name, target_zone_name)
                if conn in parallel_moves:
                    t = adjust_t(conn)
                else:
                    t = base_t

                z_start = self.map_graph.get_zones().get(start_zone_name)
                z_target = self.map_graph.get_zones().get(target_zone_name)

                if z_start and z_target:
                    p1 = self._to_pixels(z_start.x, z_start.y)
                    p2 = self._to_pixels(z_target.x, z_target.y)
                    current_pixel_pos = self._lerp(p1, p2, t)
                    self._draw_abstract_drone(current_pixel_pos, drone.id)

            for d_id, drone in in_transit.items():
                if not drone.current_location:
                    self.curr_drones_pos[d_id] = self.prev_drones_pos[d_id]
                    start_zone_name = self.prev_drones_pos.get(d_id)
                    target_zone_name = drone.path[0][0]
                else:
                    start_zone_name = self.prev_drones_pos.get(d_id)
                    target_zone_name = drone.current_location

                if not start_zone_name or not target_zone_name:
                    continue
                conn = self.map_graph.get_connection(
                        start_zone_name, target_zone_name)
                if conn in parallel_moves:
                    t = adjust_t(conn)
                else:
                    t = base_t

                z_start = self.map_graph.get_zones().get(start_zone_name)
                z_target = self.map_graph.get_zones().get(target_zone_name)

                if z_start and z_target:
                    p1 = self._to_pixels(z_start.x, z_start.y)
                    p2 = self._to_pixels(z_target.x, z_target.y)
                    p_middle = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)

                    if not drone.current_location:
                        current_pixel_pos = self._lerp(p1, p_middle, t)
                    else:
                        current_pixel_pos = self._lerp(p_middle, p2, t)

                    self._draw_abstract_drone(current_pixel_pos, drone.id)

            for name, docked in docked_groups.items():
                dock = docked[:8]
                zone = self.map_graph.get_zones().get(name)
                if zone:
                    for d_idx, dro in enumerate(dock, 1):
                        docked_pos = self._get_dock_position(
                            self._to_pixels(zone.x, zone.y), d_idx, len(dock))
                        self._draw_abstract_drone(docked_pos, dro)
            pygame.display.flip()
            clock.tick(60)

        self.draw_static_map()
        for d_id, drone in in_transit.items():
            if drone.current_location:
                if drone.current_location not in docked_groups:
                    docked_groups[drone.current_location] = []
                docked_groups[drone.current_location].append(d_id)
        for d in moving_drones.values():
            if d.current_location:
                if d.current_location not in docked_groups:
                    docked_groups[d.current_location] = []
                docked_groups[d.current_location].append(d.id)
        for name, docked in docked_groups.items():
            excess = len(docked) - 8
            dock = docked[:8]
            zone = self.map_graph.get_zones().get(name)
            rad = self.radious
            if zone:
                for d_idx, dro in enumerate(dock, 1):
                    if dro in in_transit:
                        in_transit.pop(dro)
                    docked_pos = self._get_dock_position(
                            self._to_pixels(zone.x, zone.y), d_idx, len(dock))
                    self._draw_abstract_drone(docked_pos, dro)
                if excess > 0:
                    line = "+" + str(excess)
                    pos = self._to_pixels(zone.x, zone.y)
                    excess_surf = self.font.render(
                            line, True, get_rgb("white"))
                    excess_rect = excess_surf.get_rect(
                        midtop=(pos[0] + rad, pos[1] - 2 * rad)
                    )
                    self.screen.blit(excess_surf, excess_rect)
        for d_id, drone in in_transit.items():
            start_zone_name = self.prev_drones_pos.get(d_id)
            target_zone_name = drone.path[0][0]
            if not start_zone_name or not target_zone_name:
                continue
            z_start = self.map_graph.get_zones().get(start_zone_name)
            z_target = self.map_graph.get_zones().get(target_zone_name)

            if z_start and z_target:
                p1 = self._to_pixels(z_start.x, z_start.y)
                p2 = self._to_pixels(z_target.x, z_target.y)
                p_middle = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
                self._draw_abstract_drone(p_middle, drone.id)

        pygame.display.flip()
