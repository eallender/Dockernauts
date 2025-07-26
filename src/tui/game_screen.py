import random
from io import StringIO
from tui.assets.planet_templates import PLANET_TEMPLATES
from config import AppConfig

from textual.screen import Screen
from textual.widgets import Static
from textual.reactive import reactive
from textual.containers import Container
from textual.app import ComposeResult
from textual.containers import Horizontal

CONFIG = AppConfig().get_config()


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
        self.status_callback = None  # Add callback for status updates

    def set_status_callback(self, callback):
        """Set a callback function to update status"""
        self.status_callback = callback

    def on_mount(self):
        self.set_interval(1 / 30, self.refresh_display)

    def pan(self, dx: int, dy: int):
        self.offset_x += dx * 2  # move 2 columns per horizontal step (slower horizontal movement)
        self.offset_y += dy      
        self.needs_render = True
        
        # Update sector when panning
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
        buf = StringIO()

        # Cache of what's drawn so planets can overwrite it
        char_grid = [[" "] * width for _ in range(height)]

        # draw stars first 
        for row in range(height):
            y = oy + row
            for col in range(width):
                x = ox + col
                seed = (x * 92837111 + y * 689287) & 0xFFFFFFFF
                rng = random.Random(seed)
                char_grid[row][col] = (
                    rng.choice(self.star_chars) if rng.random() < self.density else " "
                )

        # generate and draw planets 
        self._populate_visible_planets(ox, oy, width, height)

        for (px, py), planet in self.planets.items():
            for dy, line in enumerate(planet["art"]):
                for dx, ch in enumerate(line):
                    gx, gy = px + dx, py + dy
                    sx, sy = gx - ox, gy - oy
                    if 0 <= sx < width and 0 <= sy < height and ch != " ":
                        char_grid[sy][sx] = ch

        for row in char_grid:
            buf.write("".join(row) + "\n")

        self.update(buf.getvalue())
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
                    if rng.random() < 0.8:  # 10% chance to place a planet
                        template = rng.choice(self.planet_templates)
                        planet_w = max(len(line) for line in template)
                        planet_h = len(template)

                        if planet_w > sector_w or planet_h > sector_w:
                            print(f"Skipping planet too large ({planet_w}x{planet_h}) for sector size {sector_w}")
                            continue  # skip this planet or resize sector_w accordingly

                        planet_x = sx * sector_w + rng.randint(0, sector_w - planet_w)
                        planet_y = sy * sector_w + rng.randint(0, sector_w - planet_h)
                        self.planets[(planet_x, planet_y)] = {
                            "art": template,
                        }

class StatusBar(Horizontal):
    fuel = reactive(100)
    gold = reactive(50)
    sector_x = reactive(0)
    sector_y = reactive(0)

    def __init__(self):
        super().__init__()
        self.fuel_display = Static("⛽ Fuel: 0", id="fuel")
        self.gold_display = Static("🪙 Gold: 0", id="gold") 
        self.sector_display = Static("🗺️ Sector: (0,0)", id="sector")

        for display in [self.fuel_display, self.gold_display, self.sector_display]:
            display.styles.height = 1
            display.styles.max_height = 1

    def compose(self) -> ComposeResult:
        yield self.fuel_display
        yield self.gold_display
        yield self.sector_display

    def on_mount(self):
        self.watch_fuel(self.fuel)
        self.watch_gold(self.gold)
        self.watch_sector_x(self.sector_x)
        self.watch_sector_y(self.sector_y)

    def watch_fuel(self, value):
        self.fuel_display.update(f"⛽ Fuel: {value}")

    def watch_gold(self, value):
        self.gold_display.update(f"🪙 Gold: {value}")

    def watch_sector_x(self, value):
        self.sector_display.update(f"🗺️ Sector: ({value},{self.sector_y})")

    def watch_sector_y(self, value):
        self.sector_display.update(f"🗺️ Sector: ({self.sector_x},{value})")



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
        self.set_interval(0.5, self.update_status)
        space_view.update_sector_position()

    def update_sector_from_space_view(self, sector_x, sector_y):
        """Called by SpaceView when sector changes"""
        self.status.sector_x = sector_x
        self.status.sector_y = sector_y

    def update_status(self):
        self.status.fuel = 97 # TODO: Replace with feedback from game master
        self.status.gold = 120

    def action_pan(self, direction: str) -> None:
        view = self.query_one(SpaceView)
        match direction:
            case "up": view.pan(0, -1)
            case "down": view.pan(0, 1)
            case "left": view.pan(-1, 0)
            case "right": view.pan(1, 0)