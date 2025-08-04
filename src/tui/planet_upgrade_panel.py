from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from textual.widgets import Static, Button

from planet import Planet


class UpgradeButton(Button):
    """Custom button for planet upgrades with resource type and cost info"""
    
    def __init__(self, resource_type: str, cost: int, **kwargs):
        self.resource_type = resource_type
        self.cost = cost
        super().__init__(f"Upgrade {resource_type.title()} ({cost}g)", **kwargs)
        self.styles.margin = (0, 1)
        self.styles.padding = (0, 1)


class PlanetUpgradePanel(Vertical):
    """Panel with interactive buttons for upgrading planet resource production"""
    
    # Reactive properties
    planet_name = reactive("")
    food_cost = reactive(100)
    gold_cost = reactive(100) 
    metal_cost = reactive(100)
    is_panel_visible = reactive(False)
    
    def __init__(self):
        super().__init__()
        self.visible = False
        self.current_planet_data = None
        
        # Create upgrade buttons
        self.title_display = Static("▌ PLANET UPGRADES ▐")
        self.title_display.add_class("upgrade-panel-title")
        
        self.divider1 = Static("━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.divider1.add_class("upgrade-divider")
        
        # Buttons will be created dynamically based on current costs
        self.food_button = UpgradeButton("food", 100)
        self.food_button.add_class("upgrade-food")
        
        self.gold_button = UpgradeButton("gold", 100)
        self.gold_button.add_class("upgrade-gold")
        
        self.metal_button = UpgradeButton("metal", 100)
        self.metal_button.add_class("upgrade-metal")
        
        self.instructions = Static("Tab/Shift+Tab: Navigate  Enter: Upgrade")
        self.instructions.add_class("upgrade-instructions")
        
        self.divider2 = Static("━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.divider2.add_class("upgrade-divider")
        
        # Track which button is focused
        self.focused_button_index = 0
        self.buttons = [self.food_button, self.gold_button, self.metal_button]
        
        # Style components
        for widget in [self.title_display, self.divider1, self.divider2, self.instructions]:
            widget.styles.height = 1
            widget.styles.max_height = 1
    
    def compose(self) -> ComposeResult:
        yield self.title_display
        yield self.divider1
        
        # Button container
        button_container = Vertical()
        button_container.add_class("upgrade-button-container")
        with button_container:
            yield self.food_button
            yield self.gold_button
            yield self.metal_button
        
        yield button_container
        yield self.divider2
        yield self.instructions
    
    def on_mount(self):
        """Set up reactive watchers and initial state"""
        self.watch_food_cost(self.food_cost)
        self.watch_gold_cost(self.gold_cost)
        self.watch_metal_cost(self.metal_cost)
        
        # Initially hidden
        self.hide_panel()
        
        # Set initial focus
        self.update_button_focus()
    
    def watch_food_cost(self, value):
        if hasattr(self, 'food_button'):
            self.food_button.label = f"Upgrade Food ({value}g)"
    
    def watch_gold_cost(self, value):  
        if hasattr(self, 'gold_button'):
            self.gold_button.label = f"Upgrade Gold ({value}g)"
    
    def watch_metal_cost(self, value):
        if hasattr(self, 'metal_button'):
            self.metal_button.label = f"Upgrade Metal ({value}g)"
    
    def show_panel(self, planet_info, planet_data=None, preserve_focus=True):
        """Show the upgrade panel for the selected planet"""
        self.planet_name = planet_info.get("name", "Unknown Planet")
        self.current_planet_data = planet_data
        
        # Calculate upgrade costs (for now, simple fixed costs)
        # TODO: Make this dynamic based on current upgrade levels
        self.food_cost = 100
        self.gold_cost = 150
        self.metal_cost = 200
        
        self.visible = True
        self.is_panel_visible = True
        self.styles.display = "block"
        
        # Only reset focus if explicitly requested (e.g., first time opening panel)
        if not preserve_focus:
            self.focused_button_index = 0
        
        self.update_button_focus()
    
    def hide_panel(self):
        """Hide the upgrade panel"""
        self.visible = False
        self.is_panel_visible = False
        self.styles.display = "none"
        self.current_planet_data = None
    
    def cycle_button_focus(self, direction=1):
        """Cycle focus between upgrade buttons"""
        if not self.visible:
            return
        
        # Clear current focus
        self.buttons[self.focused_button_index].remove_class("focused")
        
        # Move to next/previous button
        self.focused_button_index = (self.focused_button_index + direction) % len(self.buttons)
        
        # Set new focus
        self.update_button_focus()
    
    def update_button_focus(self):
        """Update visual focus state of buttons"""
        if not self.visible:
            return
            
        # Clear all focus states
        for button in self.buttons:
            button.remove_class("focused")
        
        # Set focus on current button
        self.buttons[self.focused_button_index].add_class("focused")
    
    def activate_focused_button(self):
        """Activate the currently focused upgrade button"""
        if not self.visible:
            return False
        
        focused_button = self.buttons[self.focused_button_index]
        resource_type = focused_button.resource_type
        cost = focused_button.cost
        
        # TODO: Implement actual upgrade logic with resource checking
        # For now, just return the upgrade information
        return {
            "resource_type": resource_type,
            "cost": cost,
            "planet_name": self.planet_name,
            "planet_data": self.current_planet_data
        }
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        if event.button in self.buttons:
            # Find which button was pressed and set focus to it
            self.focused_button_index = self.buttons.index(event.button)
            self.update_button_focus()
            
            # Activate the button
            upgrade_info = self.activate_focused_button()
            if upgrade_info:
                # Post a custom event that the parent can handle
                self.post_message(UpgradeRequested(upgrade_info))


class UpgradeRequested:
    """Custom message for when an upgrade is requested"""
    
    def __init__(self, upgrade_info):
        self.upgrade_info = upgrade_info