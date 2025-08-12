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
Welcome to Dockernauts! You are a space captain exploring an infinite galaxy filled with diverse planets and resources. Your mission is to survive by managing your resources, claiming planets that spawn Docker containers, and building your space empire before your food supplies run out!

## 🎮 Controls

### Movement
- ⬆️ **Arrow Up** - Move up through space
- ⬇️ **Arrow Down** - Move down through space  
- ⬅️ **Arrow Left** - Move left through space
- ➡️ **Arrow Right** - Move right through space

### Planet Interaction
- **Tab** - Switch between/cycle through nearby planets
- **E** - Open planet information window for the selected planet
- **Enter** - Activate selected options (claim planets, confirm upgrades)
- **↑/↓** - Navigate upgrade options (when upgrade panel is open)

### General Controls
- **Q** - Quit/Go back to previous screen
- **Escape** - Return to previous screen/menu

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

### 🍎 Resources & Survival
Manage three key resources displayed in your status bar:

- 🍎 **Food** - Essential for survival (decreases over time) - **GAME OVER when it reaches zero!**
- 🏆 **Gold** - Currency for claiming planets and upgrades  
- 🔧 **Metal** - Materials for construction and upgrades

**Survival Mechanics:**
- Food consumption occurs over time - manage your supplies carefully!
- Start each new game with 250 of each resource
- Monitor your food constantly to avoid starvation!

### 🌍 Planet Claiming & Docker Integration
Use **Tab** to select planets, then **E** to open detailed information:

**Planet Discovery:**
- Use **Tab** to cycle through and select nearby planets
- Press **E** to open the information window for the selected planet
- Each planet shows type, size, coordinates, and distance
- Claiming costs vary based on distance from origin (0,0)

**Planet Claiming:**
- Spend gold to claim planets and establish outposts
- **Each claimed planet spawns a real Docker container!**
- Claimed planets generate resources over time via NATS messaging
- Distance pricing: farther planets cost more
- Size multiplier affects cost: Small=1x, Medium=1.5x, Large=2x

**Planet Upgrades:**
- Upgrade claimed planets to increase resource production
- Multiple upgrade levels available for enhanced efficiency
- Use **↑/↓ arrows** to navigate upgrade options
- Press **Enter** to confirm upgrades (costs metal)
- Strategic upgrade decisions affect your empire's growth

### Status Information
- **Sector Coordinates**: Shows your current galactic position
- **Resource Counters**: Track your Food, Gold, and Metal supplies

## 💡 Survival Tips

1. **Monitor your food** 🍎 - It decreases over time, game over when it hits zero!
2. **Claim planets strategically** 🏆 - Balance gold spending with resource generation
3. **Upgrade wisely** 🔧 - Enhanced planets produce more resources
4. **Explore efficiently** 📍 - Each sector is 100x100 units with distributed planets
5. **Planet Selection**: Use **Tab** to cycle through planets, **E** to open their info windows
6. **Visual Feedback**: Selected planets are highlighted with borders
7. **Claiming Strategy**: Start near origin (0,0) - cheaper planets, then expand outward
8. **Size Matters**: Small planets cost less but may have different resource potential
9. **Gold Management**: Balance between claiming new planets and upgrading existing ones
10. **Plan your empire** 🌌 - Different planet types offer various strategic advantages
11. **Watch the clock** ⏰ - Survival time contributes to your final score
12. **Docker Integration**: Each claimed planet creates a real container that generates resources!

## 🚀 Getting Started

1. **Launch the game** - You'll start at the title screen
2. **Start exploring** - Begin in space sector (0,0) with 250 of each resource
3. **Navigate the universe** - Use arrow keys to pan around space
4. **Discover planets** - Watch for colorful planets as you explore
5. **Interact with planets** - Press **Tab** to select planets, then **E** to open their details
6. **Claim planets** - Spend gold to claim planets and spawn Docker containers
7. **Manage resources** - Monitor your food supply to avoid starvation!
8. **Upgrade planets** - Enhance claimed planets to boost resource production
9. **Survive as long as possible** - Food decreases over time - don't let it reach zero!
10. **Game Over** - When food runs out, see your survival time and final score

## 🎯 Game Objective

**Primary Goal**: Survive as long as possible while building your space empire!

**Win Conditions**: There is no traditional "win" - the goal is to:
- Survive as long as possible before food runs out
- Claim and upgrade as many planets as possible
- Achieve the highest score based on survival time and resources collected
- Build an efficient Docker container empire

**Game Over**: When food reaches zero, you'll see:
- Your total survival time
- Your final score calculation
- Options to play again or return to main menu

---

## 🎨 Visual Legend

```
Space Elements:
✦ · * ⋆     - Stars and stellar objects (background)
ASCII Art   - Planets (Tab to select, E to open info, Enter to claim/upgrade)
Borders     - Selection indicators around chosen planets
Sectors     - 100x100 coordinate grid system

Status Bar:
🍎 Food: X  🏆 Gold: X  🔧 Metal: X  📍 Sector: (X,Y)
```

---

**Good luck, Space Captain! Survive the infinite galaxy and build your Docker empire!**

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
