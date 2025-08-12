![Dockernauts](static/imgs/title-screen.png)

**A Terminal-Based Space Exploration Game**

Created for a Boot.dev hackathon,
Dockernauts is an immersive ASCII-based space exploration game built with Python and Textual. Navigate through a procedurally generated universe, discover colorful planets, manage resources, claim planets that spawn Docker containers, and build your space empire while surviving in the harsh depths of space!

## Features

### Infinite Space Exploration

Procedurally Generated Universe: Explore an endless cosmos with algorithmically placed planets and star systems  
Smooth Panning: Navigate seamlessly through space with arrow key controls  
Sector-Based Coordinates: Track your location with a sector-based positioning system  

![planets](static/imgs/planets.png)

### Resource Management & Survival

**Real-time Status Bar**: Monitor your vital resources at all times
- 🍎 **Food supplies** - Essential for survival (decreases over time)
- 🏆 **Gold reserves** - Currency for claiming planets and upgrades  
- 🔧 **Metal stockpiles** - Materials for construction and upgrades
- 📍 **Current sector coordinates** - Track your location in the universe

**Survival Mechanics**: 
- Food consumption occurs over time - manage your supplies carefully!
- When food reaches zero, it's **GAME OVER** 
- Start each new game with 250 of each resource
- Resources reset properly between games

### Planet Interaction & Claims

**Planet Discovery & Claiming**:
- Select on planets to view detailed information
- Claim planets for a cost in gold to establish outposts
- Each claimed planet spawns a **real Docker container**
- Claimed planets generate resources over time via NATS messaging

**Planet Upgrades**:
- Upgrade your claimed planets to increase resource production
- Multiple upgrade levels available for enhanced efficiency
- Strategic upgrade decisions affect your empire's growth

## Installation

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/)
- [Docker](https://www.docker.com/) and Docker Compose
- Terminal with Unicode support

### Setup
**Clone the repository**
```bash 
git clone https://github.com/eallender/Dockernauts.git
cd dockernauts
```

### Install dependencies
```bash
poetry install
```

### Run the game

**🚀 Easy start (recommended):**
```bash
# Linux/Mac
./start.sh

# Windows
start.bat
```

The start scripts automatically:
- ✅ Check all prerequisites (Python, Poetry, Docker)
- ✅ Install dependencies if needed
- ✅ Start Docker services (`docker compose up --build -d`)
- ✅ Launch the game
- ✅ Clean up Docker containers when you exit

**Manual start:**
```bash
# Start Docker services first
docker compose up --build -d

# Then run the game
poetry run python src/main.py

# Clean up when done
docker compose down
```

## How to Play

### 🎮 Controls

**Movement**:
- ⬆️ **Arrow Up** - Move up through space
- ⬇️ **Arrow Down** - Move down through space  
- ⬅️ **Arrow Left** - Move left through space
- ➡️ **Arrow Right** - Move right through space

**Interaction**:
- **Tab** - Select/focus planets for interaction
- **Enter** - Activate selected options
- **Q** - Quit/Go back to previous screen

**Planet Management**:
- **↑/↓** - Navigate upgrade options (when upgrade panel is open)
- **Enter** - Confirm upgrades or actions

### 🚀 Getting Started

1. **Launch the game** - You'll start at the title screen
2. **Start exploring** - Begin in space sector (0,0) with 250 of each resource
3. **Navigate the universe** - Use arrow keys to pan around space
4. **Discover planets** - Watch for colorful planets as you explore
5. **Interact with planets** - Toggle selection on planets to see their details
6. **Claim planets** - Spend gold to claim planets and spawn Docker containers
7. **Manage resources** - Monitor your food supply to avoid starvation!
8. **Upgrade planets** - Enhance claimed planets to boost resource production

## 🛠️ Technical Features

**Architecture**:
- **Procedural Generation** - Seeded random universe for consistent exploration
- **Efficient Rendering** - Only renders visible areas for smooth performance  
- **Event-Driven Design** - Clean separation between UI and game logic
- **Microservices** - NATS messaging between game components
- **Containerization** - Real Docker containers for claimed planets
- **Modular Design** - Easy to extend with new features

**Backend Systems**:
- **Master Station** - Central resource management and game state
- **NATS Messaging** - Real-time communication between services
- **Docker Integration** - Dynamic container creation for planet claims
- **Resource Tracking** - Persistent resource management across game sessions
- **Automatic Cleanup** - Smart container lifecycle management

## 🚧 Current Status & Roadmap

### ✅ Completed Features
- ✅ **Core Game Loop** - Full exploration, claiming, upgrading cycle
- ✅ **Survival Mechanics** - Food consumption and game over system
- ✅ **Docker Integration** - Real containers spawn for claimed planets
- ✅ **Planet Upgrades** - Multi-level upgrade system for resource production
- ✅ **Resource Management** - Complete economic system with persistent state
- ✅ **Game Over System** - Beautiful end screen with restart functionality
- ✅ **Start Scripts** - Automated setup and Docker orchestration
- ✅ **NATS Messaging** - Real-time communication between game components