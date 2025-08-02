import os
import random

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Button, Static

from tui.game_screen import SpaceScreen
from tui.intructions import InstructionsScreen
from utils.config import AppConfig
from utils.nats import NatsClient

CONFIG = AppConfig().get_config()
NATS_ADDRESS = os.getenv("NATS_ADDRESS", "nats://localhost:4222")


class StarField(Static):
    """Custom widget that generates stars to fill its container."""

    def __init__(self, density: float = 0.1, update_interval: float = 1, **kwargs):
        super().__init__(**kwargs)
        self.density = density
        self.star_chars = [".", "*", "·", "✦", "✧", "⋆"]
        self.update_interval = update_interval
        self._timer: Timer | None = None
        self.can_focus = False

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


class TitleScreen(Screen):
    CSS_PATH = f"{CONFIG.get('root')}/static/screens/title.css"

    BINDINGS = [
        ("up", "previous_button", "Previous"),
        ("down", "next_button", "Next"),
        ("enter", "select_button", "Select"),
    ]

    def __init__(self, nats_client, **kwargs):
        super().__init__(**kwargs)
        self.nats_client = nats_client
        self.current_button_index = 0
        self.button_ids = ["start", "instructions", "exit"]

    def compose(self) -> ComposeResult:
        yield SmallScreenMsg()
        # Top starfield
        yield StarField(id="top-stars")

        yield Horizontal(
            StarField(id="left-stars"),
            Vertical(
                Static(
                    """
╔══════════════════════════════════════════════════════════════════════════════╗
║   ██████╗  ██████╗  ██████╗██╗  ██╗███████╗██████╗ ███╗   ██╗ █████╗ ██╗   ██╗████████╗███████╗   ║
║   ██╔══██╗██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗████╗  ██║██╔══██╗██║   ██║╚══██╔══╝██╔════╝   ║
║   ██║  ██║██║   ██║██║     █████╔╝ █████╗  ██████╔╝██╔██╗ ██║███████║██║   ██║   ██║   ███████╗   ║
║   ██║  ██║██║   ██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗██║╚██╗██║██╔══██║██║   ██║   ██║   ╚════██║   ║
║   ██████╔╝╚██████╔╝╚██████╗██║  ██╗███████╗██║  ██║██║ ╚████║██║  ██║╚██████╔╝   ██║   ███████║   ║
║   ╚═════╝  ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚══════╝   ║
╚══════════════════════════════════════════════════════════════════════════════╝
                """,
                    id="game-title",
                ),
                Static("◊ GALACTIC CONQUEST AWAITS ◊", id="subtitle"),
                Container(
                    Button("🚀 START EXPLORING", id="start"),
                    Button("📖 HOW TO PLAY", id="instructions"),
                    Button("❌ EXIT TO VOID", id="exit"),
                    id="menu-buttons",
                ),
                Static(
                    "[ Press ENTER to select • Press Q to quit • Use ↑↓ to navigate ]",
                    id="status-bar",
                ),
                id="center-content",
            ),
            StarField(id="right-stars"),
            id="main-layout",
        )

        # Bottom starfield
        yield StarField(id="bottom-stars")

    def on_mount(self) -> None:
        """Focus the first button when the screen loads"""
        self.update_button_focus()

    def update_button_focus(self):
        """Update which button has focus based on current_button_index"""
        try:
            # Remove focus from all buttons first
            for button_id in self.button_ids:
                button = self.query_one(f"#{button_id}")
                button.remove_class("focused")

            current_button = self.query_one(
                f"#{self.button_ids[self.current_button_index]}"
            )
            current_button.focus()
            current_button.add_class("focused")
        except Exception:
            pass

    def action_previous_button(self) -> None:
        """Move to previous button"""
        self.current_button_index = (self.current_button_index - 1) % len(
            self.button_ids
        )
        self.update_button_focus()

    def action_next_button(self) -> None:
        """Move to next button"""
        self.current_button_index = (self.current_button_index + 1) % len(
            self.button_ids
        )
        self.update_button_focus()

    def action_select_button(self) -> None:
        """Select the currently focused button"""
        current_button_id = self.button_ids[self.current_button_index]
        if current_button_id == "start":
            self.app.push_screen(SpaceScreen(nats_client=self.nats_client))
        elif current_button_id == "instructions":
            self.app.push_screen(InstructionsScreen())
        elif current_button_id == "exit":
            self.app.exit()

    def on_resize(self, event: events.Resize) -> None:
        width = event.size.width

        min_screen_width = 110  # Below this: show small screen message
        min_star_screen_width = 115  # Below this: hide side stars
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
                ratio = (clamped_width - min_star_screen_width) / (
                    max_screen_width - min_star_screen_width
                )
                side_width = int(
                    ratio * (max_side_width - min_side_width) + min_side_width
                )

                for star in left_stars:
                    star.styles.width = side_width
                    star.display = True
                for star in right_stars:
                    star.styles.width = side_width
                    star.display = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            self.app.push_screen(SpaceScreen(nats_client=self.nats_client))
        elif event.button.id == "exit":
            self.app.exit()
        elif event.button.id == "instructions":
            self.app.push_screen(InstructionsScreen())


class DockernautsApp(App):
    BINDINGS = [("q", "quit", "Quit")]

    async def on_mount(self) -> None:
        self.nats_client = NatsClient(NATS_ADDRESS, subject="game.state")
        await self.nats_client.connect()
        self.push_screen(TitleScreen(nats_client=self.nats_client))

    def action_back(self) -> None:
        """Handle escape key to go back"""
        if len(self.screen_stack) > 1:
            self.pop_screen()


if __name__ == "__main__":
    app = DockernautsApp()
    app.run()
