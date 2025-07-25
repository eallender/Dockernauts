import os
import random
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Button
from textual.screen import Screen
from config import AppConfig

CONFIG = AppConfig().get_config()

class StarField(Static):
    """Animated starfield for screen edges"""
    
    def __init__(self, width=20, height=30, **kwargs):
        self.width = width
        self.height = height
        super().__init__(self.generate_stars(), **kwargs)
    
    def generate_stars(self):
        """Generate random star field"""
        star_chars = ["✦", "✧", "⋆", "✩", "★", ".", "·", "∘", "*", "+"]
        lines = []
        
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                if random.random() < 0.06:  # 6% chance of star
                    line += random.choice(star_chars)
                else:
                    line += " "
            lines.append(line)
        
        return "\n".join(lines)
        
    def on_mount(self):
        self.set_interval(1, self.update_stars)
        
    def update_stars(self):
        self.update(self.generate_stars())

# ---------- Screens ----------
class TitleScreen(Screen):
    CSS_PATH = f"{CONFIG.get('root')}/static/screens/title.css"

    def compose(self) -> ComposeResult:
        # Top starfield
        yield StarField(width=80, height=4, id="top-stars")
        
        yield Horizontal(
            StarField(width=20, height=30, id="left-stars"),
            
            Vertical(
                Static("""
╔══════════════════════════════════════════════════════════════════════════════╗
║   ██████╗  ██████╗  ██████╗██╗  ██╗███████╗██████╗ ███╗   ██╗ █████╗ ██╗   ██╗████████╗███████╗   ║
║   ██╔══██╗██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗████╗  ██║██╔══██╗██║   ██║╚══██╔══╝██╔════╝   ║
║   ██║  ██║██║   ██║██║     █████╔╝ █████╗  ██████╔╝██╔██╗ ██║███████║██║   ██║   ██║   ███████╗   ║
║   ██║  ██║██║   ██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗██║╚██╗██║██╔══██║██║   ██║   ██║   ╚════██║   ║
║   ██████╔╝╚██████╔╝╚██████╗██║  ██╗███████╗██║  ██║██║ ╚████║██║  ██║╚██████╔╝   ██║   ███████║   ║
║   ╚═════╝  ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚══════╝   ║
╚══════════════════════════════════════════════════════════════════════════════╝
                """, id="game-title"),
                
                Static("◊ GALACTIC CONQUEST AWAITS ◊", id="subtitle"),
                
                Container(
                    Button("🚀 START EXPLORING", id="start"),
                    Button("🌍 GALAXY MAP", id="galaxy"),
                    Button("❌ EXIT TO VOID", id="exit"),
                    id="menu-buttons"
                ),
                
                Static("[ Press ENTER to select • Press Q to quit • Use ↑↓ to navigate ]", id="status-bar"),
                
                id="center-content"
            ),
            
            StarField(width=20, height=30, id="right-stars"),
            
            id="main-layout"
        )
        
        # Bottom starfield
        yield StarField(width=80, height=4, id="bottom-stars")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            self.app.push_screen(GalaxyScreen())
        elif event.button.id == "exit":
            self.app.exit()
        elif event.button.id == "galaxy":
            self.app.push_screen(GalaxyScreen())

class GalaxyScreen(Screen):
    CSS_PATH = f"{CONFIG.get('root')}/static/screens/galaxy.css"
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield StarField(id="galaxy-stars")
        yield Static("""
╔═══════════════════ GALAXY SECTOR 7-Alpha ═══════════════════╗
║                                                               ║
║        🪐 TERRA        🛸 MARS         🌑 LUNA               ║
║         [⚡120]        [⛽ 89]        [🔬 45]               ║
║                                                               ║
║        🪐 EUROPA       🪐 TITAN       🛸 KEPLER             ║
║         [❄️ 67]        [⛽234]        [🔬156]               ║
║                                                               ║  
║  Legend: ⚡Energy  ⛽Fuel  🔬Research  ❄️Ice  🏭Industry    ║
╚═══════════════════════════════════════════════════════════════╝
        """, id="map")
        yield Button("Enter Terra", id="terra")
        yield StarField(width=80, height=3, id="galaxy-stars-bottom")
        yield Footer()

# ---------- App ----------
class DockernautsApp(App):
    BINDINGS = [
        ("q", "quit", "Quit")
    ]

    def on_mount(self) -> None:
        self.push_screen(TitleScreen())

    def action_back(self) -> None:
        """Handle escape key to go back"""
        if len(self.screen_stack) > 1:
            self.pop_screen()

if __name__ == "__main__":
    app = DockernautsApp()
    app.run()