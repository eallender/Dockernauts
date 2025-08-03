import json
import random

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.events import Click
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Static

from tui.assets.planet_templates import PLANET_TEMPLATES
from utils.config import AppConfig
from utils.logger import Logger

CONFIG = AppConfig().get_config()
logger = Logger(__name__).get_logger()

PLANET_TYPES = {
    "desert": {"color": "yellow", "name": "Desert World"},
    "ocean": {"color": "blue", "name": "Ocean World"},
    "forest": {"color": "green", "name": "Forest World"},
    "ice": {"color": "cyan", "name": "Ice World"},
    "volcanic": {"color": "red", "name": "Volcanic World"},
    "gas_giant": {"color": "purple", "name": "Gas Giant"},
    "rocky": {"color": "white", "name": "Rocky World"},
    "crystal": {"color": "magenta", "name": "Crystal World"},
}


class SpaceView(Static):
    def __init__(self):
        super().__init__()
        self.offset_x = 0
        self.offset_y = 0
        self.density = 0.03
        self.star_chars = ["✦", ".", "·", " "]
        self.planets = {}
        self.planet_templates = PLANET_TEMPLATES
        self.planet_sector_size = 100
        self.needs_render = True
        self.status_callback = None
        self.planet_click_callback = None
        
        # Planet selection for keyboard interaction
        self.selected_planet = None
        self.nearby_planets = []

    def set_status_callback(self, callback):
        """Set a callback function to update status"""
        self.status_callback = callback

    def set_planet_click_callback(self, callback):
        """Set a callback function for when planets are clicked"""
        self.planet_click_callback = callback

    def on_mount(self):
        # Reduce refresh rate from 30 FPS to 15 FPS for better performance
        self.set_interval(1 / 15, self.refresh_display)

    # Mouse clicking disabled due to terminal compatibility issues
    # Use keyboard controls instead: Tab to cycle, E to select nearest, Enter to interact

    def get_planet_at_position(self, world_x, world_y):
        """Check if the given world coordinates are on a planet with improved collision detection"""
        for planet_key, planet in self.planets.items():
            px, py = planet["position"]
            planet_w = planet["width"]
            planet_h = planet["height"]

            # Use larger bounding box for easier clicking (25% padding)
            padding = max(2, min(planet_w, planet_h) // 4)
            
            # Check if click is within expanded planet bounds
            if (px - padding <= world_x < px + planet_w + padding and 
                py - padding <= world_y < py + planet_h + padding):
                
                return {
                    "position": (px, py),
                    "world_coords": (world_x, world_y),
                    "art": planet["art"],
                    "type": planet.get("type", "rocky"),
                    "color": planet.get("color", "white"),
                    "sector": planet["sector"],
                    "name": planet.get("name", "Unknown Planet"),
                    "key": planet_key,
                }
        return None

    def get_nearby_planets(self, visible_only=True):
        """Get planets that are visible on screen or near screen center"""
        width, height = self.size.width, self.size.height
        if width <= 0 or height <= 0:
            return []
        
        center_x = self.offset_x + width // 2
        center_y = self.offset_y + height // 2
        
        nearby = []
        for planet_key, planet in self.planets.items():
            px, py = planet["position"]
            planet_w, planet_h = planet["width"], planet["height"]
            
            if visible_only:
                # Check if planet is at least partially visible on screen
                # Planet is visible if any part overlaps with screen bounds
                planet_left = px
                planet_right = px + planet_w
                planet_top = py
                planet_bottom = py + planet_h
                
                screen_left = self.offset_x
                screen_right = self.offset_x + width
                screen_top = self.offset_y
                screen_bottom = self.offset_y + height
                
                # Check for overlap (planet is visible)
                if (planet_right > screen_left and planet_left < screen_right and
                    planet_bottom > screen_top and planet_top < screen_bottom):
                    
                    # Calculate distance from screen center for sorting
                    distance = ((px - center_x) ** 2 + (py - center_y) ** 2) ** 0.5
                    nearby.append({
                        "key": planet_key,
                        "distance": distance,
                        "planet": planet
                    })
            else:
                # Original behavior - distance-based selection
                distance = ((px - center_x) ** 2 + (py - center_y) ** 2) ** 0.5
                if distance <= 200:  # max_distance fallback
                    nearby.append({
                        "key": planet_key,
                        "distance": distance,
                        "planet": planet
                    })
        
        # Sort by distance (closest first)
        nearby.sort(key=lambda p: p["distance"])
        return nearby

    def select_nearest_planet(self):
        """Select the planet nearest to screen center (visible planets only)"""
        nearby = self.get_nearby_planets(visible_only=True)
        if nearby:
            self.selected_planet = nearby[0]["key"]
            self.needs_render = True
            return self.planets[self.selected_planet]
        return None

    def cycle_planet_selection(self, direction=1):
        """Cycle through visible planets only (direction: 1=next, -1=previous)"""
        self.nearby_planets = self.get_nearby_planets(visible_only=True)
        if not self.nearby_planets:
            self.selected_planet = None
            return None
        
        if self.selected_planet is None:
            # Select first visible planet
            self.selected_planet = self.nearby_planets[0]["key"]
        else:
            # Find current selection in visible planets and move to next/previous
            current_index = -1
            for i, planet_data in enumerate(self.nearby_planets):
                if planet_data["key"] == self.selected_planet:
                    current_index = i
                    break
            
            if current_index >= 0:
                # Current selection is visible, cycle to next/previous
                new_index = (current_index + direction) % len(self.nearby_planets)
                self.selected_planet = self.nearby_planets[new_index]["key"]
            else:
                # Current selection not visible anymore, select first visible planet
                self.selected_planet = self.nearby_planets[0]["key"]
        
        self.needs_render = True
        return self.planets[self.selected_planet]

    def interact_with_selected_planet(self):
        """Interact with the currently selected planet"""
        if self.selected_planet and self.selected_planet in self.planets:
            planet = self.planets[self.selected_planet]
            if self.planet_click_callback:
                planet_info = {
                    "position": planet["position"],
                    "type": planet["type"],
                    "color": planet["color"],
                    "sector": planet["sector"],
                    "name": planet["name"],
                    "key": self.selected_planet,
                }
                self.planet_click_callback(planet_info)
                return True
        return False

    def pan(self, dx: int, dy: int):
        self.offset_x += dx * 2
        self.offset_y += dy
        self.needs_render = True
        
        # Clear selection if currently selected planet is no longer visible
        if self.selected_planet:
            visible_planets = self.get_nearby_planets(visible_only=True)
            visible_keys = [p["key"] for p in visible_planets]
            if self.selected_planet not in visible_keys:
                self.selected_planet = None

        if self.status_callback:
            self.update_sector_position()

    def update_sector_position(self):
        """Calculate current sector based on screen center"""
        width, height = self.size.width, self.size.height
        if width <= 0 or height <= 0:
            return

        center_x = self.offset_x + width // 2
        center_y = self.offset_y + height // 2
        sector_x = center_x // self.planet_sector_size
        sector_y = center_y // self.planet_sector_size * -1

        self.status_callback(sector_x, sector_y)

    def refresh_display(self):
        if not self.needs_render:
            return

        width, height = self.size.width, self.size.height
        if width <= 0 or height <= 0:
            return

        ox, oy = self.offset_x, self.offset_y

        # Create a Rich Text object for colored output
        text = Text()

        # Cache of what's drawn so planets can overwrite it
        char_grid = [[" "] * width for _ in range(height)]
        color_grid = [["#4a9eff"] * width for _ in range(height)]  # Default star color

        # Draw stars with simple optimization - reuse Random instance
        star_rng = random.Random()
        for row in range(height):
            y = oy + row
            for col in range(width):
                x = ox + col
                seed = (x * 92837111 + y * 689287) & 0xFFFFFFFF
                star_rng.seed(seed)
                char_grid[row][col] = (
                    star_rng.choice(self.star_chars)
                    if star_rng.random() < self.density
                    else " "
                )

        # Generate and draw planets
        self._populate_visible_planets(ox, oy, width, height)

        for planet_key, planet in self.planets.items():
            px, py = planet["position"]
            planet_color = planet.get("color", "white")
            
            # Highlight selected planet
            is_selected = (planet_key == self.selected_planet)
            if is_selected:
                planet_color = f"bold bright_{planet_color}"
            
            for dy, line in enumerate(planet["art"]):
                for dx, ch in enumerate(line):
                    gx, gy = px + dx, py + dy
                    sx, sy = gx - ox, gy - oy
                    if 0 <= sx < width and 0 <= sy < height and ch != " ":
                        char_grid[sy][sx] = ch
                        color_grid[sy][sx] = planet_color
            
            # Add selection indicator around planet
            if is_selected:
                planet_w, planet_h = planet["width"], planet["height"]
                # Draw bright selection border with corner markers
                # Top and bottom borders
                for border_x in range(px - 2, px + planet_w + 2):
                    for border_y in [py - 2, py + planet_h + 1]:
                        sx, sy = border_x - ox, border_y - oy
                        if 0 <= sx < width and 0 <= sy < height:
                            if char_grid[sy][sx] == " ":
                                char_grid[sy][sx] = "═"
                                color_grid[sy][sx] = "bright_cyan"
                
                # Left and right borders
                for border_y in range(py - 2, py + planet_h + 2):
                    for border_x in [px - 2, px + planet_w + 1]:
                        sx, sy = border_x - ox, border_y - oy
                        if 0 <= sx < width and 0 <= sy < height:
                            if char_grid[sy][sx] == " ":
                                char_grid[sy][sx] = "║"
                                color_grid[sy][sx] = "bright_cyan"
                
                # Corner markers for extra visibility
                corners = [(px - 2, py - 2), (px + planet_w + 1, py - 2), 
                          (px - 2, py + planet_h + 1), (px + planet_w + 1, py + planet_h + 1)]
                for corner_x, corner_y in corners:
                    sx, sy = corner_x - ox, corner_y - oy
                    if 0 <= sx < width and 0 <= sy < height:
                        char_grid[sy][sx] = "▣"
                        color_grid[sy][sx] = "bright_magenta"

        # Build colored text output
        for row in range(height):
            for col in range(width):
                char = char_grid[row][col]
                color = color_grid[row][col]
                text.append(char, style=color)
            if row < height - 1:  # Don't add newline after last row
                text.append("\n")

        self.update(text)
        self.needs_render = False

    def _populate_visible_planets(self, ox, oy, width, height):
        sector_w = self.planet_sector_size
        min_sector_x = (ox) // sector_w
        max_sector_x = (ox + width) // sector_w
        min_sector_y = (oy) // sector_w
        max_sector_y = (oy + height) // sector_w

        for sx in range(min_sector_x, max_sector_x + 1):
            for sy in range(min_sector_y, max_sector_y + 1):
                sector_key = f"sector_{sx}_{sy}"
                if sector_key not in self.planets:
                    rng = random.Random((sx * 99991 + sy * 31337) & 0xFFFFFFFF)
                    # Reduced planet density for better performance and realism
                    if rng.random() < 0.4:
                        template = rng.choice(self.planet_templates)
                        planet_w = max(len(line) for line in template)
                        planet_h = len(template)

                        if planet_w > sector_w or planet_h > sector_w:
                            logger.debug(
                                f"Skipping planet too large ({planet_w}x{planet_h}) for sector size {sector_w}"
                            )
                            continue

                        planet_type = rng.choice(list(PLANET_TYPES.keys()))
                        planet_info = PLANET_TYPES[planet_type]

                        planet_x = sx * sector_w + rng.randint(0, sector_w - planet_w)
                        planet_y = sy * sector_w + rng.randint(0, sector_w - planet_h)
                        # Store planets using consistent sector-based keys
                        self.planets[sector_key] = {
                            "art": template,
                            "type": planet_type,
                            "color": planet_info["color"],
                            "name": planet_info["name"],
                            "position": (planet_x, planet_y),
                            "sector": (sx, sy),
                            "width": planet_w,
                            "height": planet_h,
                        }


class StatusBar(Horizontal):
    food = reactive(0)
    gold = reactive(0)
    metal = reactive(0)
    sector_x = reactive(0)
    sector_y = reactive(0)

    def __init__(self):
        super().__init__()
        self.food_display = Static("Food: 0", id="food")
        self.gold_display = Static("Gold: 0", id="gold")
        self.metal_display = Static("Metal: 0", id="metal")
        self.sector_display = Static("Sector: (0,0)", id="sector")
        self.controls_display = Static("E=Select nearest  Tab=Cycle  Enter=Interact", id="controls")

        for display in [
            self.food_display,
            self.gold_display,
            self.metal_display,
            self.sector_display,
            self.controls_display,
        ]:
            display.styles.height = 1
            display.styles.max_height = 1

    def compose(self) -> ComposeResult:
        yield self.food_display
        yield self.gold_display
        yield self.metal_display
        yield self.sector_display
        yield self.controls_display

    def on_mount(self):
        self.watch_food(self.food)
        self.watch_gold(self.gold)
        self.watch_metal(self.metal)
        self.watch_sector_x(self.sector_x)
        self.watch_sector_y(self.sector_y)

    def watch_food(self, value):
        self.food_display.update(f"Food: {value}")

    def watch_gold(self, value):
        self.gold_display.update(f"Gold: {value}")

    def watch_metal(self, value):
        self.metal_display.update(f"Metal: {value}")

    def watch_sector_x(self, value):
        self.sector_display.update(f"Sector: ({value},{self.sector_y})")

    def watch_sector_y(self, value):
        self.sector_display.update(f"Sector: ({self.sector_x},{value})")


class SpaceScreen(Screen):
    """Full-screen star viewer. Arrow keys pan around."""

    CSS_PATH = f"{CONFIG.get('root')}/static/screens/game_screen.css"

    BINDINGS = [
        ("up", "pan('up')", "Pan Up"),
        ("down", "pan('down')", "Pan Down"),
        ("left", "pan('left')", "Pan Left"),
        ("right", "pan('right')", "Pan Right"),
        ("tab", "cycle_planets", "Next Planet"),
        ("shift+tab", "cycle_planets_reverse", "Previous Planet"),
        ("e", "select_nearest", "Select Nearest"),
        ("enter", "interact_planet", "Interact"),
        ("q", "app.pop_screen", "Back"),
    ]

    def __init__(self, nats_client, **kwargs):
        super().__init__(**kwargs)
        self.nats_client = nats_client
        self.latest_game_state = {}

    def compose(self):
        status_bar = StatusBar()
        status_bar.id = "status-bar"
        yield status_bar
        yield Container(SpaceView(), id="space-container")

    def on_mount(self) -> None:
        space_view = self.query_one(SpaceView)
        space_view.styles.width = "100%"
        space_view.styles.height = "100%"

        self.status = self.query_one(StatusBar)
        space_view.set_status_callback(self.update_sector_from_space_view)
        space_view.set_planet_click_callback(self.on_planet_clicked)
        self.set_interval(1, self.update_status)
        space_view.update_sector_position()

    def on_planet_clicked(self, planet_info):
        """Handle planet click events"""
        px, py = planet_info["position"]
        sector = planet_info["sector"]
        planet_type = planet_info.get("type", "Unknown")

        self.notify(
            f"Clicked {planet_type} planet at ({px}, {py}) in sector {sector}",
            title="Planet Selected",
            timeout=3,
        )

    def update_sector_from_space_view(self, sector_x, sector_y):
        """Called by SpaceView when sector changes"""
        self.status.sector_x = sector_x
        self.status.sector_y = sector_y

    async def request_game_state(self):
        try:
            response = await self.nats_client.nc.request("game.state", b"", timeout=1)
            data = json.loads(response.data.decode())
            self.latest_game_state = data.get("resources", {})
        except Exception as e:
            logger.error(f"Failed to request game state: {e}")

    async def update_status(self):
        await self.request_game_state()
        resources = self.latest_game_state
        self.status.food = resources.get("food", 0)
        self.status.gold = resources.get("gold", 0)
        self.status.metal = resources.get("metal", 0)

    def action_pan(self, direction: str) -> None:
        view = self.query_one(SpaceView)
        match direction:
            case "up":
                view.pan(0, -1)
            case "down":
                view.pan(0, 1)
            case "left":
                view.pan(-1, 0)
            case "right":
                view.pan(1, 0)

    def action_cycle_planets(self) -> None:
        """Cycle to next planet"""
        view = self.query_one(SpaceView)
        planet = view.cycle_planet_selection(1)
        if planet:
            self.notify(
                f"◉ {planet['name']} ({planet['type']}) - Press Enter to interact",
                title="Planet Selected",
                timeout=3,
            )
        else:
            self.notify("No planets nearby - Use arrow keys to explore", timeout=2)

    def action_cycle_planets_reverse(self) -> None:
        """Cycle to previous planet"""
        view = self.query_one(SpaceView)
        planet = view.cycle_planet_selection(-1)
        if planet:
            self.notify(
                f"◉ {planet['name']} ({planet['type']}) - Press Enter to interact",
                title="Planet Selected",
                timeout=3,
            )
        else:
            self.notify("No planets nearby - Use arrow keys to explore", timeout=2)

    def action_select_nearest(self) -> None:
        """Select nearest planet to screen center"""
        view = self.query_one(SpaceView)
        planet = view.select_nearest_planet()
        if planet:
            self.notify(
                f"◉ {planet['name']} ({planet['type']}) - Press Enter to interact",
                title="Nearest Planet Found",
                timeout=3,
            )
        else:
            self.notify("No planets nearby - Pan around to find planets!", timeout=3)

    def action_interact_planet(self) -> None:
        """Interact with selected planet"""
        view = self.query_one(SpaceView)
        if view.interact_with_selected_planet():
            self.notify("🚀 Interacting with planet...", timeout=2)
        else:
            self.notify("No planet selected - Press E to select nearest or Tab to cycle", timeout=3)
