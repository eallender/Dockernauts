from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from textual.widgets import Static, Button


class ClaimButton(Button):
    """Custom button for claiming planets with cost info"""
    
    def __init__(self, cost: int, **kwargs):
        self.cost = cost
        super().__init__(f"Claim Planet ({cost}g)", **kwargs)
        self.styles.margin = (0, 1)
        self.styles.padding = (0, 1)


class PlanetClaimPanel(Vertical):
    """Panel for claiming unclaimed planets with distance-based pricing"""
    
    # Reactive properties
    planet_name = reactive("")
    claim_cost = reactive(100)
    distance = reactive(0)
    planet_size = reactive("small")
    is_panel_visible = reactive(False)
    
    def __init__(self):
        super().__init__()
        self.visible = False
        self.current_planet_data = None
        
        # Create claim UI
        self.title_display = Static("▌ CLAIM PLANET ▐")
        self.title_display.add_class("claim-panel-title")
        
        self.divider1 = Static("━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.divider1.add_class("claim-divider")
        
        # Planet info display
        self.planet_info = Static("")
        self.planet_info.add_class("claim-info")
        
        self.distance_info = Static("")
        self.distance_info.add_class("claim-distance")
        
        self.cost_info = Static("")
        self.cost_info.add_class("claim-cost")
        
        # Claim button will be created dynamically based on current cost
        self.claim_button = ClaimButton(100)
        self.claim_button.add_class("claim-button")
        
        self.instructions = Static("Enter: Claim Planet  Q: Cancel")
        self.instructions.add_class("claim-instructions")
        
        self.divider2 = Static("━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.divider2.add_class("claim-divider")
        
        # Style components
        for widget in [self.title_display, self.divider1, self.divider2, self.instructions]:
            widget.styles.height = 1
            widget.styles.max_height = 1
        
        for widget in [self.planet_info, self.distance_info, self.cost_info]:
            widget.styles.height = 1
            widget.styles.max_height = 1
    
    def compose(self) -> ComposeResult:
        yield self.title_display
        yield self.divider1
        yield self.planet_info
        yield self.distance_info
        yield self.cost_info
        
        # Button container
        button_container = Vertical()
        button_container.add_class("claim-button-container")
        with button_container:
            yield self.claim_button
        
        yield button_container
        yield self.divider2
        yield self.instructions
    
    def on_mount(self):
        """Set up reactive watchers and initial state"""
        self.watch_planet_name(self.planet_name)
        self.watch_claim_cost(self.claim_cost) 
        self.watch_distance(self.distance)
        self.watch_planet_size(self.planet_size)
        
        # Initially hidden
        self.hide_panel()
    
    def watch_planet_name(self, value):
        if hasattr(self, 'planet_info'):
            self.planet_info.update(f"Planet: {value} ({self.planet_size.upper()})")
    
    def watch_claim_cost(self, value):
        if hasattr(self, 'claim_button'):
            self.claim_button.label = f"Claim Planet ({value}g)"
            self.claim_button.cost = value
    
    def watch_distance(self, value):
        if hasattr(self, 'distance_info'):
            self.distance_info.update(f"Distance from Origin: {value:.1f} units")
    
    def watch_planet_size(self, value):
        if hasattr(self, 'planet_info'):
            self.planet_info.update(f"Planet: {self.planet_name} ({value.upper()})")
    
    def show_panel(self, planet_info, planet_data=None):
        """Show the claim panel for the selected planet"""
        self.planet_name = planet_info.get("name", "Unknown Planet")
        self.current_planet_data = planet_data
        
        # Calculate distance and cost
        x, y = planet_info.get("position", (0, 0))
        import math
        self.distance = math.sqrt(x ** 2 + y ** 2)
        
        # Get planet data to determine size and cost
        if planet_data and hasattr(planet_data, 'size'):
            self.planet_size = planet_data.size.value
            self.claim_cost = planet_data.calculate_claim_cost()
        else:
            # Fallback calculation if planet_data not available
            self.planet_size = "medium"  # Default assumption
            base_cost = 100
            distance_cost = int(self.distance / 100) * 50
            size_multipliers = {"small": 1.0, "medium": 1.5, "large": 2.0}
            self.claim_cost = int((base_cost + distance_cost) * size_multipliers[self.planet_size])
        
        # Update cost display (simple)
        self.cost_info.update(f"Claim Cost: {self.claim_cost} gold")
        
        self.visible = True
        self.is_panel_visible = True
        self.styles.display = "block"
    
    def hide_panel(self):
        """Hide the claim panel"""
        self.visible = False
        self.is_panel_visible = False
        self.styles.display = "none"
        self.current_planet_data = None
    
    def activate_claim_button(self):
        """Activate the claim button"""
        if not self.visible:
            return False
        
        # Return claim information
        return {
            "action": "claim",
            "cost": self.claim_cost,
            "planet_name": self.planet_name,
            "planet_data": self.current_planet_data
        }
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        if event.button == self.claim_button:
            # Activate the claim button
            claim_info = self.activate_claim_button()
            if claim_info:
                # Post a custom event that the parent can handle
                self.post_message(ClaimRequested(claim_info))


class ClaimRequested:
    """Custom message for when a planet claim is requested"""
    
    def __init__(self, claim_info):
        self.claim_info = claim_info