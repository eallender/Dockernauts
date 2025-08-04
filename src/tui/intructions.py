from rich.markdown import Markdown
from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from utils.config import AppConfig

CONFIG = AppConfig().get_config()


class InstructionsScreen(Screen):
    """Instructions screen explaining how to play the game."""

    CSS_PATH = f"{CONFIG.get('root')}/static/screens/instructions.css"

    BINDINGS = [
        ("q", "app.pop_screen", "Back to Menu"),
        ("escape", "app.pop_screen", "Back to Menu"),
    ]

    def compose(self) -> ComposeResult:
        instructions_text = """# 🚀 DOCKERNAUTS - How to Play

## Overview
Welcome to Dockernauts! You are a space captain exploring an infinite galaxy filled with diverse planets and resources. Your mission is to survive and thrive by managing your resources and discovering new worlds in the vast cosmos.

## Controls

### Navigation
- **Arrow Keys**: Pan around the galaxy OR navigate upgrade buttons
  - ↑ **Up Arrow**: Move view up / Previous upgrade button
  - ↓ **Down Arrow**: Move view down / Next upgrade button
  - ← **Left Arrow**: Move view left (disabled when upgrade panel is open)
  - → **Right Arrow**: Move view right (disabled when upgrade panel is open)

### Planet Interaction
- **Tab**: Select closest planet or cycle to next nearby planet
- **Shift+Tab**: Cycle to previous nearby planet
- **E**: Toggle planet info and upgrade panels
- **Enter**: Activate upgrade button (when upgrade panel is open)

### General Controls
- **Q**: Return to previous screen/menu
- **Escape**: Return to previous screen/menu

## Game Elements

### The Galaxy
The galaxy is an infinite procedurally generated space filled with:
- **Stars**: Background stellar objects (✦, ·, *, ⋆)
- **Planets**: Interactive worlds of different types
- **Sectors**: The galaxy is divided into 100x100 coordinate sectors

### Planet Types
You'll encounter various planet types, each with unique characteristics:

**Desert Worlds** - Harsh, arid planets with hidden resources  
**Ocean Worlds** - Water-covered planets rich in life  
**Forest Worlds** - Lush, green planets with abundant food  
**Ice Worlds** - Frozen, crystalline planets with rare minerals  
**Volcanic Worlds** - Fiery, molten planets with valuable metals  
**Gas Giants** - Massive gaseous planets with energy resources  
**Rocky Worlds** - Barren, mineral-rich planets for mining  
**Crystal Worlds** - Rare, crystalline planets with precious gems  

### Resources
Manage three key resources displayed in your status bar:

- **Food**: Essential for survival and crew maintenance
- **Gold**: Universal currency for trading and upgrades  
- **Metal**: Raw materials for additional upgrades

### Planet Upgrades
When you select a planet with **Tab**, both an info panel and upgrade panel appear automatically:

- **Info Panel**: Shows planet details (type, size, coordinates, resources, status)
- **Upgrade Panel**: Contains buttons to upgrade resource production rates
- **Navigation**: Use **Up/Down arrows** to cycle through upgrade buttons
- **Activation**: Press **Enter** to purchase the selected upgrade (costs gold)
- **Panel Toggle**: Press **E** to hide/show both panels

### Status Information
- **Sector Coordinates**: Shows your current galactic position
- **Resource Counters**: Track your Food, Gold, and Metal supplies

## Gameplay Tips

1. **Explore Systematically**: Each sector may contain planets - explore thoroughly
2. **Planet Selection**: Use **Tab** to select the closest planet, then **Tab** again to cycle through visible planets
3. **Visual Feedback**: Selected planets are highlighted with bright cyan borders and corner markers
4. **Planet Management**: Press **E** to view planet details and upgrade options
5. **Upgrade Strategy**: Use gold to upgrade planet resource production rates
6. **Resource Management**: Keep an eye on your Food, Gold, and Metal levels
7. **Navigate Efficiently**: Use arrow keys to move quickly across space
8. **Sector Awareness**: Note your coordinates to remember interesting locations
9. **Planet Variety**: Different planet types offer different resources and challenges

## Getting Started

1. From the title screen, select "🚀 START EXPLORING"
2. Use arrow keys to move around and explore the galaxy
3. Look for planets in each sector (they appear as detailed ASCII art)
4. Press **Tab** to select the closest planet (both info and upgrade panels appear automatically)
5. Continue pressing **Tab** to cycle through visible planets
6. Use **Up/Down arrows** to navigate upgrade buttons, **Enter** to purchase upgrades
7. Monitor your resources in the status bar at the top
8. Press **E** to hide panels and continue exploring, or keep them open while planet hopping
9. Press Q to return to the main menu when done exploring

## Visual Legend

```
Space Symbols:
✦ · * ⋆     - Stars and stellar objects
ASCII Art   - Planets (selectable with E/Tab, interact with Enter)
═══║║▣      - Cyan selection borders and corner markers around selected planets
Sectors     - 100x100 coordinate grid system

Status Bar:
Food: X  Gold: X  Metal: X  Sector: (X,Y)  Tab=Planets  Arrows=Pan/Navigate  E=Toggle  Enter=Upgrade
```

---

**Good luck, Space Captain! The infinite galaxy awaits your exploration.**

*Press Q or Escape to return to the main menu*
"""

        yield Header()
        with Container(id="instructions-container"):
            with ScrollableContainer(id="scroll-container"):
                yield Static(Markdown(instructions_text), id="instructions-content")
        yield Footer()

    def on_mount(self) -> None:
        # Focus the scrollable container for keyboard navigation
        scroll_container = self.query_one("#scroll-container")
        scroll_container.focus()
