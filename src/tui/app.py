import random
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Button
from textual.screen import Screen
from textual import events
from textual.timer import Timer
from config import AppConfig
from tui.save_manager import SaveManager


CONFIG = AppConfig().get_config()

class StarField(Static):
    """Custom widget that generates stars to fill its container."""

    def __init__(self, density: float = 0.1, update_interval: float = 1, **kwargs):
        super().__init__(**kwargs)
        self.density = density
        self.star_chars = [".", "*", "·", "✦", "✧", "⋆"]
        self.update_interval = update_interval
        self._timer: Timer | None = None

    def on_mount(self) -> None:
        """Called when widget is first mounted."""
        self.call_after_refresh(self.generate_stars)
        self._timer = self.set_interval(self.update_interval, self.generate_stars)

    def on_resize(self, event) -> None:
        """Regenerate stars when resized."""
        self.generate_stars()

    def generate_stars(self) -> None:
        """Generate stars based on current container size."""
        width, height = self.size.width, self.size.height
        if width <= 0 or height <= 0:
            return

        stars = []
        for row in range(height):
            line = []
            for col in range(width):
                if random.random() < self.density:
                    star = random.choice(self.star_chars)
                else:
                    star = " "
                line.append(star)
            stars.append("".join(line))

        self.update("\n".join(stars))

class SmallScreenMsg(Static):
    def __init__(self):
        super().__init__("Please enlarge your window to see the title screen.")
        self.id = "small-screen-msg"
        self.styles.color = "red"
        self.styles.text_align = "center"
        self.styles.padding = (1, 2)

# ---------- Screens ----------
class TitleScreen(Screen):
    CSS_PATH = f"{CONFIG.get('root')}/static/screens/title.css"

    def compose(self) -> ComposeResult:
        yield SmallScreenMsg()
        # Top starfield
        yield StarField(id="top-stars")
        
        yield Horizontal(
            StarField(id="left-stars"),
            
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
            
            StarField(id="right-stars"),
            
            id="main-layout"
        )
        
        # Bottom starfield
        yield StarField(id="bottom-stars")

    def on_resize(self, event: events.Resize) -> None:
        width = event.size.width

        min_screen_width = 110          # Below this: show small screen message
        min_star_screen_width = 115     # Below this: hide side stars
        max_screen_width = 150
        min_side_width = 1
        max_side_width = 20

        small_screen_msg = self.query_one("#small-screen-msg")
        main_layout = self.query_one("#main-layout")
        left_stars = self.query("#left-stars")
        right_stars = self.query("#right-stars")

        if width < min_screen_width:
            main_layout.display = False
            small_screen_msg.display = True

            for star in left_stars:
                star.display = False
            for star in right_stars:
                star.display = False

        else:
            main_layout.display = True
            small_screen_msg.display = False

            if width < min_star_screen_width:
                for star in left_stars:
                    star.display = False
                for star in right_stars:
                    star.display = False
            else:
                clamped_width = max(min_star_screen_width, min(max_screen_width, width))
                ratio = (clamped_width - min_star_screen_width) / (max_screen_width - min_star_screen_width)
                side_width = int(ratio * (max_side_width - min_side_width) + min_side_width)

                for star in left_stars:
                    star.styles.width = side_width
                    star.display = True
                for star in right_stars:
                    star.styles.width = side_width
                    star.display = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            self.app.push_screen(SaveManager())
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