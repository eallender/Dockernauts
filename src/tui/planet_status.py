from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Static

from planet import Planet, PlanetSize


class PlanetStatusWindow(Vertical):
    """Status window that displays detailed information about a selected planet"""
    
    # Reactive properties for planet data
    planet_name = reactive("")
    planet_type = reactive("")
    planet_size = reactive("")
    sector_coords = reactive("")
    world_coords = reactive("")
    resources = reactive({})
    is_claimed = reactive(False)
    is_discovered = reactive(False)
    
    def __init__(self):
        super().__init__()
        self.visible = False
        
        # Create display widgets
        self.title_display = Static("▌ PLANET STATUS ▐", id="planet-status-title")
        self.name_display = Static("", id="planet-name")
        self.type_display = Static("", id="planet-type")
        self.size_display = Static("", id="planet-size")
        self.coords_display = Static("", id="planet-coords")
        self.sector_display = Static("", id="planet-sector")
        self.resources_display = Static("", id="planet-resources")
        self.status_display = Static("", id="planet-claim-status")
        self.divider = Static("━━━━━━━━━━━━━━━━━━━━━━━━━", id="planet-divider")
        
        # Style all components
        for widget in [self.title_display, self.name_display, self.type_display, 
                      self.size_display, self.coords_display, self.sector_display,
                      self.resources_display, self.status_display, self.divider]:
            widget.styles.height = 1
            widget.styles.max_height = 1
    
    def compose(self) -> ComposeResult:
        yield self.title_display
        yield self.divider
        yield self.name_display
        yield self.type_display
        yield self.size_display
        yield self.coords_display
        yield self.sector_display
        yield self.resources_display
        yield self.status_display
    
    def on_mount(self):
        """Set up reactive watchers"""
        self.watch_planet_name(self.planet_name)
        self.watch_planet_type(self.planet_type)
        self.watch_planet_size(self.planet_size)
        self.watch_sector_coords(self.sector_coords)
        self.watch_world_coords(self.world_coords)
        self.watch_resources(self.resources)
        self.watch_is_claimed(self.is_claimed)
        self.watch_is_discovered(self.is_discovered)
        
        # Initially hidden
        self.hide_status()
    
    def watch_planet_name(self, value):
        if value:
            self.name_display.update(f"Name: {value}")
        else:
            self.name_display.update("")
    
    def watch_planet_type(self, value):
        if value:
            # Capitalize and format planet type
            formatted_type = value.replace("_", " ").title()
            self.type_display.update(f"Type: {formatted_type}")
        else:
            self.type_display.update("")
    
    def watch_planet_size(self, value):
        if value:
            self.size_display.update(f"Size: {value.title()}")
        else:
            self.size_display.update("")
    
    def watch_sector_coords(self, value):
        if value:
            self.sector_display.update(f"Sector: {value}")
        else:
            self.sector_display.update("")
    
    def watch_world_coords(self, value):
        if value:
            self.coords_display.update(f"Coords: {value}")
        else:
            self.coords_display.update("")
    
    def watch_resources(self, value):
        if value and isinstance(value, dict):
            food = value.get("food", 0)
            gold = value.get("gold", 0)
            metal = value.get("metal", 0)
            self.resources_display.update(f"Resources: F:{food} G:{gold} M:{metal}")
        else:
            self.resources_display.update("")
    
    def watch_is_claimed(self, value):
        self._update_status_display()
    
    def watch_is_discovered(self, value):
        self._update_status_display()
    
    def _update_status_display(self):
        """Update the status display based on claimed/discovered state"""
        if self.is_claimed:
            status = "Status: ⚫ CLAIMED"
            style = "green"
        elif self.is_discovered:
            status = "Status: ◉ DISCOVERED"
            style = "yellow"
        else:
            status = "Status: ○ UNEXPLORED"
            style = "white"
        
        self.status_display.update(status)
    
    def show_planet_info(self, planet_info, planet_data=None):
        """Display information for the selected planet"""
        # Extract basic info from the game screen planet data
        self.planet_name = planet_info.get("name", "Unknown Planet")
        self.planet_type = planet_info.get("type", "unknown")
        
        # Format coordinates
        px, py = planet_info.get("position", (0, 0))
        self.world_coords = f"({px}, {py})"
        
        # Format sector
        sector = planet_info.get("sector", (0, 0))
        self.sector_coords = f"({sector[0]}, {sector[1]})"
        
        # If we have a Planet object with detailed data, use it
        if planet_data and isinstance(planet_data, Planet):
            self.planet_size = planet_data.size.value
            self.resources = planet_data.available_resources
            self.is_claimed = planet_data.claimed
            self.is_discovered = planet_data.discovered
        else:
            # Use placeholder data for now
            self.planet_size = "unknown"
            self.resources = {"food": "?", "gold": "?", "metal": "?"}
            self.is_claimed = False
            self.is_discovered = True  # Assume discovered if we can see it
        
        self.show_status()
    
    def show_status(self):
        """Make the status window visible"""
        self.visible = True
        self.styles.display = "block"
    
    def hide_status(self):
        """Hide the status window"""
        self.visible = False
        self.styles.display = "none"
        # Clear all data
        self.planet_name = ""
        self.planet_type = ""
        self.planet_size = ""
        self.sector_coords = ""
        self.world_coords = ""
        self.resources = {}
        self.is_claimed = False
        self.is_discovered = False