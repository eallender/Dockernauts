import os
from textual import events
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

# from tui.app import TitleScreen  # Not needed - we pop back to existing title screen
from utils.config import AppConfig

CONFIG = AppConfig().get_config()


class SmallScreenMsg(Static):
    def __init__(self):
        super().__init__("Please enlarge your window to see the game over screen.")
        self.id = "small-screen-msg"
        self.styles.color = "red"
        self.styles.text_align = "center"
        self.styles.padding = (1, 2)


class GameOverScreen(Screen):
    CSS = """
    GameOverScreen {
        background: #000011;
        layout: vertical;
    }

    GameOverScreen #top-stars {
        width: 100%;
        height: 3;
        color: #4a9eff;
        background: #000011;
        text-align: left;
        dock: top;
        margin: 0;
        padding: 0;
    }

    GameOverScreen #bottom-stars {
        width: 100%;
        height: 2;
        color: #4a9eff;
        background: #000011;
        text-align: left;
        dock: bottom;
        margin: 0;
        padding: 0;
    }

    GameOverScreen #main-layout {
        layout: horizontal;
        width: 100%;
        height: auto;
        background: #000011;
        margin: 0;
        padding: 0;
    }

    GameOverScreen #left-stars, GameOverScreen #right-stars {
        height: 100%;
        color: #4a9eff;
        background: #000011;
        margin: 0;
        padding: 0;
    }

    GameOverScreen #center-content {
        width: 1fr;
        height: auto;
        background: #000011;
        padding: 1;
        align: center top;
        margin: 0;
    }

    GameOverScreen #game-title {
        width: 100%;
        color: #ff4444;
        text-style: bold;
        text-align: center;
        margin: 1 0;
        background: #000011;
        padding: 0 1;
    }

    GameOverScreen #subtitle {
        width: 100%;
        color: #ff8888;
        text-align: center;
        text-style: italic;
        margin: 0 0 2 0;
        background: #000011;
        padding: 0;
    }

    GameOverScreen #stats-container {
        width: 100%;
        height: auto;
        align: center middle;
        background: #000011;
        margin: 0 0 2 0;
        padding: 0;
    }

    GameOverScreen #game-time {
        width: 100%;
        color: #ffaa00;
        text-align: center;
        text-style: bold;
        margin: 0;
        background: #000011;
        padding: 0;
    }

    GameOverScreen #final-score {
        width: 100%;
        color: #00ff88;
        text-align: center;
        text-style: bold;
        margin: 1 0 0 0;
        background: #000011;
        padding: 0;
    }

    GameOverScreen #menu-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        background: #000011;
        margin: 0;
        padding: 0;
    }

    GameOverScreen #menu-buttons Button {
        width: 24;
        height: 3;
        margin: 0 1;
        background: rgba(51, 17, 17, 0.8);
        color: #ff4444;
        border: solid #ff8800;
        text-style: bold;
    }

    GameOverScreen #menu-buttons Button:hover {
        background: rgba(102, 34, 34, 0.9);
        color: #ffffff;
        border: solid #ff4444;
        text-style: bold;
    }

    GameOverScreen #menu-buttons Button:focus, GameOverScreen #menu-buttons Button.focused {
        background: rgba(153, 51, 51, 0.9);
        color: #ffffff;
        border: solid #ffffff;
        text-style: bold;
    }

    GameOverScreen #status-bar {
        width: 100%;
        color: #666666;
        text-align: center;
        margin: 1 0;
        background: #000011;
        padding: 0;
    }

    GameOverScreen #small-screen-msg {
        width: 100%;
        height: 100%;
        color: #ff4444;
        text-align: center;
        text-style: bold;
        background: #000011;
        align: center middle;
        display: none;
    }
    """

    BINDINGS = [
        ("up", "previous_button", "Previous"),
        ("down", "next_button", "Next"),
        ("enter", "select_button", "Select"),
    ]

    def __init__(self, game_time: str = "00:00", final_score: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.game_time = game_time
        self.final_score = final_score
        self.current_button_index = 0
        self.button_ids = ["play_again", "main_menu", "exit"]

    def compose(self) -> ComposeResult:
        from tui.app import StarField  # Import here to avoid circular imports

        yield SmallScreenMsg()
        # Top starfield
        yield StarField(id="top-stars")

        yield Horizontal(
            StarField(id="left-stars"),
            Vertical(
                Static(
                    """
╔══════════════════════════════════════════════════════════════════════════════╗
║    ██████╗  █████╗ ███╗   ███╗███████╗     ██████╗ ██╗   ██╗███████╗██████╗     ║
║   ██╔════╝ ██╔══██╗████╗ ████║██╔════╝    ██╔═══██╗██║   ██║██╔════╝██╔══██╗    ║
║   ██║  ███╗███████║██╔████╔██║█████╗      ██║   ██║██║   ██║█████╗  ██████╔╝    ║
║   ██║   ██║██╔══██║██║╚██╔╝██║██╔══╝      ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗    ║
║   ╚██████╔╝██║  ██║██║ ╚═╝ ██║███████╗    ╚██████╔╝ ╚████╔╝ ███████╗██║  ██║    ║
║    ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝     ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝    ║
╚══════════════════════════════════════════════════════════════════════════════╝
                """,
                    id="game-title",
                ),
                Static("◊ YOUR CONQUEST HAS ENDED ◊", id="subtitle"),
                Container(
                    Static(f"⏱️  TIME SURVIVED: {self.game_time}", id="game-time"),
                    Static(f"⭐ FINAL SCORE: {self.final_score:,}", id="final-score"),
                    id="stats-container",
                ),
                Container(
                    Button("🔄 PLAY AGAIN", id="play_again"),
                    Button("🏠 MAIN MENU", id="main_menu"),
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
        if current_button_id == "play_again":
            self._play_again()
        elif current_button_id == "main_menu":
            self._return_to_main_menu()
        elif current_button_id == "exit":
            self.app.exit()

    def _play_again(self) -> None:
        """Start a new game"""
        try:
            # Send game reset message via NATS and wait before starting
            self.app.call_later(self._send_game_reset_and_start)
        except Exception as e:
            self.app.logger.error(f"Error starting new game: {e}")

    async def _send_game_reset_and_start(self) -> None:
        """Send reset message and then start the game"""
        try:
            import asyncio
            
            # Send reset message first
            await self._send_game_reset()
            
            # Wait a moment for reset to be processed
            await asyncio.sleep(0.5)
            
            # Now start the game
            from tui.game_screen import SpaceScreen
            self.app.pop_screen()
            self.app.push_screen(SpaceScreen(nats_client=self.app.nats_client))
        except Exception as e:
            self.app.logger.error(f"Error in reset and start: {e}")

    async def _send_game_reset(self) -> None:
        """Send game reset message to master station"""
        try:
            import json
            from utils.nats import NatsClient
            NATS_ADDRESS = os.getenv("NATS_ADDRESS", "nats://localhost:4222")
            reset_publisher = NatsClient(NATS_ADDRESS, "game.reset")
            await reset_publisher.connect()
            
            # Use basic publish since reset messages don't need JetStream
            message = json.dumps({"action": "reset"})
            await reset_publisher.nc.publish("game.reset", message.encode())
            await reset_publisher.close()
        except Exception as e:
            self.app.logger.error(f"Failed to send game reset message: {e}")

    def _return_to_main_menu(self) -> None:
        """Return to the main menu"""
        try:
            # Pop current screen (GameOverScreen) and game screen to return to original title
            self.app.pop_screen()  # Remove GameOverScreen
            if len(self.app.screen_stack) > 1:  # If there's still a game screen
                self.app.pop_screen()  # Remove GameScreen too
        except Exception as e:
            self.app.logger.error(f"Error returning to main menu: {e}")

    def on_resize(self, event: events.Resize) -> None:
        """Handle screen resize with same logic as title screen"""
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
        """Handle button press events"""
        if event.button.id == "play_again":
            self._play_again()
        elif event.button.id == "main_menu":
            self._return_to_main_menu()
        elif event.button.id == "exit":
            self.app.exit()
