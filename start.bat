@echo off
REM Dockernauts Game Launcher for Windows
REM This script makes it easy to run the Dockernauts space exploration game

echo 🚀 Welcome to Dockernauts! 🚀
echo Starting your space exploration adventure...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Python is not installed
    echo Please install Python 3.11+ to play Dockernauts
    pause
    exit /b 1
)

REM Check if Poetry is installed
poetry --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Poetry is not installed
    echo Please install Poetry from https://python-poetry.org/docs/
    pause
    exit /b 1
)

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Docker is not installed
    echo Please install Docker from https://www.docker.com/
    pause
    exit /b 1
)

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    docker compose version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Error: Docker Compose is not available
        echo Please install Docker Compose or use a newer version of Docker
        pause
        exit /b 1
    )
)

REM Check if we're in the right directory
if not exist "pyproject.toml" (
    echo ❌ Error: Please run this script from the Dockernauts root directory
    pause
    exit /b 1
)
if not exist "compose.yaml" (
    echo ❌ Error: Please run this script from the Dockernauts root directory
    pause
    exit /b 1
)

REM Install dependencies if needed
if not exist ".venv" if not exist "poetry.lock" (
    echo 📦 Installing dependencies...
    poetry install
    if %errorlevel% neq 0 (
        echo ❌ Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Start Docker services
echo 🐳 Starting game services (Docker containers)...
docker-compose --version >nul 2>&1
if %errorlevel% equ 0 (
    docker-compose up --build -d
) else (
    docker compose up --build -d
)

if %errorlevel% neq 0 (
    echo ❌ Error: Failed to start Docker services
    echo Make sure Docker is running and you have the necessary permissions
    pause
    exit /b 1
)

echo ✅ Docker services started successfully

REM Give services a moment to start up
echo ⏳ Waiting for services to initialize...
timeout /t 3 /nobreak >nul

REM Start the game
echo 🎮 Launching Dockernauts...
echo Use Q to quit the game
echo.

poetry run python src/main.py

echo.
echo 🧹 Cleaning up Docker services...
docker-compose --version >nul 2>&1
if %errorlevel% equ 0 (
    docker-compose down
) else (
    docker compose down
)

echo.
echo 👋 Thanks for playing Dockernauts!
pause