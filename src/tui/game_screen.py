import json
import random
import time

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.events import Click
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Static

from planet import Planet
from tui.assets.planet_templates import PLANET_TEMPLATES
from tui.planet_claim_panel import ClaimRequested, PlanetClaimPanel
from tui.planet_status import PlanetStatusWindow
from tui.planet_upgrade_panel import PlanetUpgradePanel, UpgradeRequested
from utils.config import AppConfig
from utils.docker import start_planet_container
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
        self.planets = {}  # Visual planet data
        self.planet_instances = {}  # Actual Planet instances
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
            if (
                px - padding <= world_x < px + planet_w + padding
                and py - padding <= world_y < py + planet_h + padding
            ):

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
                if (
                    planet_right > screen_left
                    and planet_left < screen_right
                    and planet_bottom > screen_top
                    and planet_top < screen_bottom
                ):

                    # Calculate distance from screen center for sorting
                    distance = ((px - center_x) ** 2 + (py - center_y) ** 2) ** 0.5
                    nearby.append(
                        {"key": planet_key, "distance": distance, "planet": planet}
                    )
            else:
                # Original behavior - distance-based selection
                distance = ((px - center_x) ** 2 + (py - center_y) ** 2) ** 0.5
                if distance <= 200:  # max_distance fallback
                    nearby.append(
                        {"key": planet_key, "distance": distance, "planet": planet}
                    )

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
            is_selected = planet_key == self.selected_planet
            if is_selected:
                # Map colors to valid bright variants
                color_mapping = {
                    "yellow": "bright_yellow",
                    "blue": "bright_blue",
                    "green": "bright_green",
                    "cyan": "bright_cyan",
                    "red": "bright_red",
                    "purple": "magenta",  # purple -> magenta for terminal compatibility
                    "white": "bright_white",
                    "magenta": "bright_magenta",
                }
                mapped_color = color_mapping.get(planet_color, planet_color)
                planet_color = f"bold {mapped_color}"

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
                corners = [
                    (px - 2, py - 2),
                    (px + planet_w + 1, py - 2),
                    (px - 2, py + planet_h + 1),
                    (px + planet_w + 1, py + planet_h + 1),
                ]
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

                        # Create actual Planet instance
                        planet_instance = Planet(
                            name=planet_info["name"],
                            uuid=f"planet_{sx}_{sy}",
                            x=planet_x,
                            y=planet_y,
                        )

                        # Store both visual data and Planet instance
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
                        self.planet_instances[sector_key] = planet_instance


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
        self.controls_display = Static(
            "Tab=Planets  Arrows=Pan/Navigate  E=Toggle  Enter=Claim/Upgrade", id="controls"
        )

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
        ("up", "pan('up')", "Pan Up / Previous Upgrade"),
        ("down", "pan('down')", "Pan Down / Next Upgrade"),
        ("left", "pan('left')", "Pan Left"),
        ("right", "pan('right')", "Pan Right"),
        ("tab", "handle_tab", "Next Planet"),
        ("shift+tab", "handle_shift_tab", "Previous Planet"),
        ("e", "toggle_info_panel", "Toggle Info Panel"),
        ("enter", "handle_enter", "Activate Upgrade Button"),
        ("q", "app.pop_screen", "Back"),
    ]

    def __init__(self, nats_client, **kwargs):
        super().__init__(**kwargs)
        self.nats_client = nats_client
        self.latest_game_state = {}
        self.debug_mode = CONFIG.get("debug_mode", False)
        self.start_time = time.time()
        self.status_timer = None

    def compose(self):
        status_bar = StatusBar()
        status_bar.id = "status-bar"
        yield status_bar

        # Create main space view that fills the screen
        yield Container(SpaceView(), id="space-container")

        # Add floating status window, upgrade panel, and claim panel on top
        yield PlanetStatusWindow()
        yield PlanetUpgradePanel()
        yield PlanetClaimPanel()

    def on_mount(self) -> None:
        space_view = self.query_one(SpaceView)
        space_view.styles.width = "100%"
        space_view.styles.height = "100%"

        self.status = self.query_one(StatusBar)
        self.planet_status = self.query_one(PlanetStatusWindow)
        self.upgrade_panel = self.query_one(PlanetUpgradePanel)
        self.claim_panel = self.query_one(PlanetClaimPanel)

        space_view.set_status_callback(self.update_sector_from_space_view)
        space_view.set_planet_click_callback(self.on_planet_clicked)
        self.status_timer = self.set_interval(1, self.update_status)
        space_view.update_sector_position()

    def debug_notify(self, message, title=None, timeout=2):
        """Only show notification if debug mode is enabled"""
        if self.debug_mode:
            self.notify(message, title=title, timeout=timeout)

    def on_planet_clicked(self, planet_info):
        """Handle planet click events"""
        px, py = planet_info["position"]
        sector = planet_info["sector"]
        planet_type = planet_info.get("type", "Unknown")

        # Get planet instance if it exists
        planet_instance = self.planet_instances.get(self.selected_planet)
        
        # Show planet status window with detailed information
        self.planet_status.show_planet_info(planet_info, planet_instance)

        self.debug_notify(
            f"Selected {planet_type} planet at ({px}, {py}) in sector {sector}",
            title="Planet Selected",
            timeout=2,
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
        
        # Check if food has reached zero - trigger game over
        if self.status.food <= 0:
            self._trigger_game_over()

    def _trigger_game_over(self):
        """Trigger game over screen with current stats"""
        from tui.game_over_screen import GameOverScreen
        
        # Stop the status update timer to prevent further updates
        if self.status_timer:
            self.status_timer.stop()
        
        # Calculate game time
        elapsed = time.time() - self.start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        game_time = f"{minutes:02d}:{seconds:02d}"
        
        # Calculate score (could be based on resources, time survived, etc.)
        final_score = self.status.gold + self.status.metal + (minutes * 10)
        
        # Push game over screen
        self.app.push_screen(GameOverScreen(game_time=game_time, final_score=final_score))

    def action_pan(self, direction: str) -> None:
        # If upgrade panel is open, use up/down arrows for button navigation instead of panning
        if self.upgrade_panel.visible:
            if direction == "up":
                self.upgrade_panel.cycle_button_focus(-1)  # Previous button
                return
            elif direction == "down":
                self.upgrade_panel.cycle_button_focus(1)  # Next button
                return
            # Left/Right still disabled when upgrade panel is open
            elif direction in ["left", "right"]:
                return  # Silently ignore left/right when upgrade panel is open

        # If claim panel is open, disable all arrow keys (claim has only one button)
        if self.claim_panel.visible:
            return  # Silently ignore all directions when claim panel is open

        # Normal panning when no panels are visible
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

        # Hide status window if currently selected planet is no longer visible
        if view.selected_planet is None:
            self.planet_status.hide_status()
            self.upgrade_panel.hide_panel()
            self.claim_panel.hide_panel()

    def action_cycle_planets(self) -> None:
        """Select closest planet first, then cycle through visible planets"""
        view = self.query_one(SpaceView)

        # If no planet is selected, select the closest one
        if view.selected_planet is None:
            planet = view.select_nearest_planet()
        else:
            # If a planet is already selected, cycle to the next one
            planet = view.cycle_planet_selection(1)

        if planet:
            # Create planet_info dict for status window
            planet_info = {
                "position": planet["position"],
                "type": planet["type"],
                "color": planet["color"],
                "sector": planet["sector"],
                "name": planet["name"],
                "key": view.selected_planet,
            }
            # Show info panel and appropriate interaction panel based on claimed status
            planet_instance = view.planet_instances.get(view.selected_planet)
            self.planet_status.show_planet_info(planet_info, planet_instance)

            if planet_instance and planet_instance.claimed:
                self.upgrade_panel.show_panel(
                    planet_info, planet_instance, preserve_focus=True
                )
                self.claim_panel.hide_panel()
                panel_type = "upgrades"
            else:
                self.claim_panel.show_panel(planet_info, planet_instance)
                self.upgrade_panel.hide_panel()
                panel_type = "claim"

            self.debug_notify(
                f"◉ {planet['name']} ({planet['type']}) - Press E to toggle info/{panel_type}",
                title="Planet Selected",
                timeout=3,
            )
        else:
            self.planet_status.hide_status()
            self.debug_notify(
                "No planets nearby - Use arrow keys to explore", timeout=2
            )

    def action_cycle_planets_reverse(self) -> None:
        """Cycle to previous planet"""
        view = self.query_one(SpaceView)

        # If no planet is selected, select the closest one
        if view.selected_planet is None:
            planet = view.select_nearest_planet()
        else:
            # If a planet is already selected, cycle to the previous one
            planet = view.cycle_planet_selection(-1)

        if planet:
            # Create planet_info dict for status window
            planet_info = {
                "position": planet["position"],
                "type": planet["type"],
                "color": planet["color"],
                "sector": planet["sector"],
                "name": planet["name"],
                "key": view.selected_planet,
            }
            # Show info panel and appropriate interaction panel based on claimed status
            planet_instance = view.planet_instances.get(view.selected_planet)
            self.planet_status.show_planet_info(planet_info, planet_instance)

            if planet_instance and planet_instance.claimed:
                self.upgrade_panel.show_panel(
                    planet_info, planet_instance, preserve_focus=True
                )
                self.claim_panel.hide_panel()
                panel_type = "upgrades"
            else:
                self.claim_panel.show_panel(planet_info, planet_instance)
                self.upgrade_panel.hide_panel()
                panel_type = "claim"

            self.debug_notify(
                f"◉ {planet['name']} ({planet['type']}) - Press E to toggle info/{panel_type}",
                title="Planet Selected",
                timeout=3,
            )
        else:
            self.planet_status.hide_status()
            self.debug_notify(
                "No planets nearby - Use arrow keys to explore", timeout=2
            )

    def action_toggle_info_panel(self) -> None:
        """Toggle info panel for currently selected planet"""
        view = self.query_one(SpaceView)

        if view.selected_planet is None:
            self.debug_notify("No planet selected - Press Tab to select one", timeout=2)
            return

        # Get planet instance to check claimed status
        planet_instance = view.planet_instances.get(view.selected_planet)

        # Check if panels are currently visible
        panels_visible = self.planet_status.visible and (
            self.upgrade_panel.visible or self.claim_panel.visible
        )

        if panels_visible:
            # Hide all panels
            self.planet_status.hide_status()
            self.upgrade_panel.hide_panel()
            self.claim_panel.hide_panel()
            self.debug_notify("Panels hidden - Tab to select planets", timeout=1)
        else:
            # Show appropriate panel based on planet claimed status
            planet = view.planets.get(view.selected_planet)
            if planet and planet_instance:
                planet_info = {
                    "position": planet["position"],
                    "type": planet["type"],
                    "color": planet["color"],
                    "sector": planet["sector"],
                    "name": planet["name"],
                    "key": view.selected_planet,
                }

                # Force all panels to hide first
                self.planet_status.hide_status()
                self.upgrade_panel.hide_panel()
                self.claim_panel.hide_panel()

                # Show status window always
                self.planet_status.show_planet_info(planet_info, planet_instance)

                # Show appropriate interaction panel based on claimed status
                if planet_instance.claimed:
                    # Show upgrade panel for claimed planets
                    self.upgrade_panel.show_panel(
                        planet_info, planet_instance, preserve_focus=False
                    )
                    self.debug_notify(
                        "Claimed planet - Tab/Enter to navigate/upgrade", timeout=2
                    )
                else:
                    # Show claim panel for unclaimed planets
                    self.claim_panel.show_panel(planet_info, planet_instance)
                    self.debug_notify("Unclaimed planet - Enter to claim", timeout=2)
            else:
                self.notify("Selected planet no longer available", timeout=2)

    def action_handle_tab(self) -> None:
        """Handle Tab key - cycle planets (arrow keys handle upgrade buttons when panel is open)"""
        # Always cycle planets with Tab - arrow keys handle upgrade button navigation
        self.action_cycle_planets()

    def action_handle_shift_tab(self) -> None:
        """Handle Shift+Tab key - cycle planets backwards (arrow keys handle upgrade buttons when panel is open)"""
        # Always cycle planets with Shift+Tab - arrow keys handle upgrade button navigation
        self.action_cycle_planets_reverse()

    def action_handle_enter(self) -> None:
        """Handle Enter key - activate upgrade button or claim button if panel is open"""
        if self.upgrade_panel.visible:
            upgrade_info = self.upgrade_panel.activate_focused_button()
            if upgrade_info:
                self.process_upgrade_request(upgrade_info)
        elif self.claim_panel.visible:
            claim_info = self.claim_panel.activate_claim_button()
            if claim_info:
                # Run async claim processing
                self.run_worker(self.process_claim_request(claim_info))
        else:
            self.debug_notify("Press E to open panel for selected planet", timeout=2)

    def process_upgrade_request(self, upgrade_info):
        """Process an upgrade request"""
        resource_type = upgrade_info["resource_type"]
        cost = upgrade_info["cost"]
        planet_name = upgrade_info["planet_name"]
        planet_data = upgrade_info.get("planet_data")

        # Check if player has enough metal
        if self.latest_game_state.get("metal", 0) >= cost:
            # Process the upgrade
            self.run_worker(self._execute_upgrade(upgrade_info))
        else:
            current_metal = self.latest_game_state.get("metal", 0)
            self.notify(
                f"Not enough metal! Need {cost}, have {current_metal}",
                title="Upgrade Failed",
                timeout=3,
            )

    async def _execute_upgrade(self, upgrade_info):
        """Execute an upgrade request with resource deduction and NATS communication"""
        resource_type = upgrade_info["resource_type"]
        cost = upgrade_info["cost"]
        planet_name = upgrade_info["planet_name"]
        planet_data = upgrade_info.get("planet_data")
        
        try:
            # Double-check we still have enough metal (resources might have changed)
            current_metal = self.latest_game_state.get("metal", 0)
            if current_metal < cost:
                self.notify(
                    f"Upgrade failed: Not enough metal! Need {cost}, have {current_metal}",
                    title="Insufficient Resources",
                    timeout=3,
                )
                return
            
            # Deduct metal from player resources via NATS JetStream
            deduct_message = {
                "gold": 0,
                "food": 0,
                "metal": -cost,  # Negative value to subtract
            }
            js = self.nats_client.nc.jetstream()
            await js.publish(
                "MASTER.resources", json.dumps(deduct_message).encode()
            )

            # Send upgrade command to the planet's Docker container via NATS
            if planet_data and hasattr(planet_data, 'uuid'):
                upgrade_command = {
                    "resource_type": resource_type,
                    "cost": cost,
                    "timestamp": time.time()
                }
                
                await js.publish(
                    f"PLANETS.{planet_data.uuid}.upgrades",
                    json.dumps(upgrade_command).encode()
                )
                
                # Apply upgrade locally (the container will also apply it)
                if hasattr(planet_data, '_apply_upgrade'):
                    planet_data._apply_upgrade(resource_type)
                
                # Update upgrade costs in the UI panel
                if self.upgrade_panel.current_planet_data == planet_data:
                    self.upgrade_panel.show_panel(
                        {"name": planet_name}, 
                        planet_data, 
                        preserve_focus=True
                    )

                self.notify(
                    f"Upgraded {resource_type} on {planet_name} for {cost} metal!",
                    title="Upgrade Successful",
                    timeout=3,
                )
            else:
                self.notify(
                    "Error: Planet data not available for upgrade",
                    title="Upgrade Failed", 
                    timeout=3,
                )
                
        except Exception as e:
            logger.error(f"Failed to execute upgrade: {e}")
            self.notify(
                f"Upgrade failed: {str(e)}",
                title="Upgrade Error",
                timeout=3,
            )

    async def process_claim_request(self, claim_info):
        """Process a planet claim request"""
        cost = claim_info["cost"]
        planet_name = claim_info["planet_name"]
        planet_data = claim_info["planet_data"]

        # Check if player has enough gold
        if self.latest_game_state.get("gold", 0) >= cost:
            # Attempt to claim the planet
            if planet_data and planet_data.claim_planet(cost):
                # Deduct gold from player resources via NATS JetStream
                try:
                    deduct_message = {
                        "gold": -cost,
                        "food": 0,
                        "metal": 0,
                    }  # Negative value to subtract
                    js = self.nats_client.nc.jetstream()
                    await js.publish(
                        "MASTER.resources", json.dumps(deduct_message).encode()
                    )

                    # Start Docker container for the claimed planet
                    try:
                        nats_address = getattr(self.nats_client, 'url', 'nats://localhost:4222')
                        container = start_planet_container(planet_name, planet_data.uuid, nats_address)
                        if container:
                            self.notify(
                                f"Successfully claimed {planet_name} for {cost} gold! Container started.",
                                title="Planet Claimed",
                                timeout=3,
                            )
                        else:
                            self.notify(
                                f"Claimed {planet_name} for {cost} gold but failed to start container",
                                title="Planet Claimed - Warning",
                                timeout=3,
                            )
                    except Exception as docker_error:
                        logger.error(f"Failed to start Docker container for planet {planet_name}: {docker_error}")
                        self.notify(
                            f"Claimed {planet_name} for {cost} gold but Docker container failed to start",
                            title="Planet Claimed - Warning",
                            timeout=3,
                        )
                    
                    # Hide claim panel and show status only
                    self.claim_panel.hide_panel()
                    # Refresh the panel display to show upgrade panel
                    self.action_toggle_info_panel()
                    self.action_toggle_info_panel()
                except Exception as e:
                    logger.error(f"Failed to deduct gold via NATS: {e}")
                    self.notify(
                        f"Claimed {planet_name} but failed to update resources",
                        title="Warning",
                        timeout=3,
                    )
            else:
                self.notify(
                    f"Failed to claim {planet_name}",
                    title="Claim Failed",
                    timeout=3,
                )
        else:
            self.notify(
                f"Not enough gold! Need {cost}g but only have {self.latest_game_state.get('gold', 0)}g",
                title="Insufficient Funds",
                timeout=3,
            )

    def on_upgrade_requested(self, message: UpgradeRequested) -> None:
        """Handle custom upgrade requested message"""
        self.process_upgrade_request(message.upgrade_info)

    def on_claim_requested(self, message: ClaimRequested) -> None:
        """Handle custom claim requested message"""
        self.run_worker(self.process_claim_request(message.claim_info))
