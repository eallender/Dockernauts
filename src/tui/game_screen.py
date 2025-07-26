import random
import time
from io import StringIO
from tui.assets.planet_templates import PLANET_TEMPLATES

from textual.screen import Screen
from textual.widgets import Static
from textual.reactive import reactive
from textual.containers import Container
from textual import events


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

    def on_mount(self):
        self.set_interval(1 / 30, self.refresh_display)

    def pan(self, dx: int, dy: int):
        self.offset_x += dx * 2  # move 2 columns per horizontal step
        self.offset_y += dy      # keep vertical step as 1 row
        self.needs_render = True

    def refresh_display(self):
        if not self.needs_render:
            return

        width, height = self.size.width, self.size.height
        if width <= 0 or height <= 0:
            return

        ox, oy = self.offset_x, self.offset_y
        buf = StringIO()

        # Cache of what’s drawn so planets can overwrite it
        char_grid = [[" "] * width for _ in range(height)]

        # --- Draw stars first ---
        for row in range(height):
            y = oy + row
            for col in range(width):
                x = ox + col
                seed = (x * 92837111 + y * 689287) & 0xFFFFFFFF
                rng = random.Random(seed)
                char_grid[row][col] = (
                    rng.choice(self.star_chars) if rng.random() < self.density else " "
                )

        # --- Generate & draw planets ---
        self._populate_visible_planets(ox, oy, width, height)

        for (px, py), planet in self.planets.items():
            for dy, line in enumerate(planet["art"]):
                for dx, ch in enumerate(line):
                    gx, gy = px + dx, py + dy
                    sx, sy = gx - ox, gy - oy
                    if 0 <= sx < width and 0 <= sy < height and ch != " ":
                        char_grid[sy][sx] = ch

        # --- Convert grid to string ---
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


class SpaceScreen(Screen):
    """Full-screen star viewer. Arrow keys pan around."""

    BINDINGS = [
        ("up", "pan('up')", "Pan Up"),
        ("down", "pan('down')", "Pan Down"),
        ("left", "pan('left')", "Pan Left"),
        ("right", "pan('right')", "Pan Right"),
        ("q", "app.pop_screen", "Back"),
    ]

    def compose(self):
        yield Container(
            SpaceView(),
            id="space-container"
        )

    def on_mount(self) -> None:
        space_view = self.query_one(SpaceView)
        space_view.styles.width = "100%"
        space_view.styles.height = "100%"

    def action_pan(self, direction: str) -> None:
        view = self.query_one(SpaceView)
        match direction:
            case "up": view.pan(0, -1)
            case "down": view.pan(0, 1)
            case "left": view.pan(-1, 0)
            case "right": view.pan(1, 0)
