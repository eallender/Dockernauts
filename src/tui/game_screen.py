import random
from tui.assets.planet_templates import PLANET_TEMPLATES
from config import AppConfig

from textual.screen import Screen
from textual.widgets import Static
from textual.reactive import reactive
from textual.containers import Container
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.events import Click
from rich.text import Text

CONFIG = AppConfig().get_config()

PLANET_TYPES = {
    "desert": {"color": "yellow", "name": "Desert World"},
    "ocean": {"color": "blue", "name": "Ocean World"},
    "forest": {"color": "green", "name": "Forest World"},
    "ice": {"color": "cyan", "name": "Ice World"},
    "volcanic": {"color": "red", "name": "Volcanic World"},
    "gas_giant": {"color": "purple", "name": "Gas Giant"},
    "rocky": {"color": "grey", "name": "Rocky World"},
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

    def set_status_callback(self, callback):
        """Set a callback function to update status"""
        self.status_callback = callback

    def set_planet_click_callback(self, callback):
        """Set a callback function for when planets are clicked"""
        self.planet_click_callback = callback

    def on_mount(self):
        self.set_interval(1 / 30, self.refresh_display)

    def on_click(self, event: Click) -> None:
        """Handle mouse clicks to detect planet interactions"""
        if not self.planet_click_callback:
            return
            
        # Convert screen coordinates to world coordinates
        world_x = self.offset_x + event.x
        world_y = self.offset_y + event.y
        
        clicked_planet = self.get_planet_at_position(world_x, world_y)
        if clicked_planet:
            self.planet_click_callback(clicked_planet)

    def get_planet_at_position(self, world_x, world_y):
        """Check if the given world coordinates are on a planet"""
        for (px, py), planet in self.planets.items():
            planet_art = planet["art"]
            planet_w = max(len(line) for line in planet_art)
            planet_h = len(planet_art)
            
            # Check if click is within planet bounds
            if px <= world_x < px + planet_w and py <= world_y < py + planet_h:
                # Check if click is on a non-space character
                art_x, art_y = world_x - px, world_y - py
                if 0 <= art_y < len(planet_art) and 0 <= art_x < len(planet_art[art_y]):
                    if planet_art[art_y][art_x] != " ":
                        return {
                            "position": (px, py),
                            "world_coords": (world_x, world_y),
                            "art": planet_art,
                            "type": planet.get("type", "rocky"),
                            "color": planet.get("color", "white"),
                            "sector": (px // self.planet_sector_size, py // self.planet_sector_size)
                        }
        return None

    def pan(self, dx: int, dy: int):
        self.offset_x += dx * 2
        self.offset_y += dy      
        self.needs_render = True
        
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

        # Draw stars first 
        for row in range(height):
            y = oy + row
            for col in range(width):
                x = ox + col
                seed = (x * 92837111 + y * 689287) & 0xFFFFFFFF
                rng = random.Random(seed)
                char_grid[row][col] = (
                    rng.choice(self.star_chars) if rng.random() < self.density else " "
                )

        # Generate and draw planets 
        self._populate_visible_planets(ox, oy, width, height)

        for (px, py), planet in self.planets.items():
            planet_color = planet.get("color", "white")
            for dy, line in enumerate(planet["art"]):
                for dx, ch in enumerate(line):
                    gx, gy = px + dx, py + dy
                    sx, sy = gx - ox, gy - oy
                    if 0 <= sx < width and 0 <= sy < height and ch != " ":
                        char_grid[sy][sx] = ch
                        color_grid[sy][sx] = planet_color

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
                if (sx, sy) not in self.planets:
                    rng = random.Random((sx * 99991 + sy * 31337) & 0xFFFFFFFF)
                    if rng.random() < 0.8:
                        template = rng.choice(self.planet_templates)
                        planet_w = max(len(line) for line in template)
                        planet_h = len(template)

                        if planet_w > sector_w or planet_h > sector_w:
                            print(f"Skipping planet too large ({planet_w}x{planet_h}) for sector size {sector_w}")
                            continue

                        planet_type = rng.choice(list(PLANET_TYPES.keys()))
                        planet_info = PLANET_TYPES[planet_type]

                        planet_x = sx * sector_w + rng.randint(0, sector_w - planet_w)
                        planet_y = sy * sector_w + rng.randint(0, sector_w - planet_h)
                        self.planets[(planet_x, planet_y)] = {
                            "art": template,
                            "type": planet_type,
                            "color": planet_info["color"],
                            "name": planet_info["name"]
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

        for display in [self.food_display, self.gold_display, self.metal_display, self.sector_display]:
            display.styles.height = 1
            display.styles.max_height = 1

    def compose(self) -> ComposeResult:
        yield self.food_display
        yield self.gold_display
        yield self.metal_display
        yield self.sector_display

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
        ("q", "app.pop_screen", "Back"),
    ]

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
        self.set_interval(0.5, self.update_status)
        space_view.update_sector_position()

    def on_planet_clicked(self, planet_info):
        """Handle planet click events"""
        px, py = planet_info["position"]
        sector = planet_info["sector"]
        planet_type = planet_info.get("type", "Unknown")
        
        self.notify(
            f"Clicked {planet_type} planet at ({px}, {py}) in sector {sector}",
            title="Planet Selected",
            timeout=3
        )

    def update_sector_from_space_view(self, sector_x, sector_y):
        """Called by SpaceView when sector changes"""
        self.status.sector_x = sector_x
        self.status.sector_y = sector_y

    def update_status(self):
        self.status.food = 97 # TODO: Replace with feedback from game master
        self.status.gold = 120
        self.status.metal = 100

    def action_pan(self, direction: str) -> None:
        view = self.query_one(SpaceView)
        match direction:
            case "up": view.pan(0, -1)
            case "down": view.pan(0, 1)
            case "left": view.pan(-1, 0)
            case "right": view.pan(1, 0)