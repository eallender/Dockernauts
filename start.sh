#!/bin/bash

# Dockernauts Game Launcher
# This script makes it easy to run the Dockernauts space exploration game

echo "🚀 Welcome to Dockernauts! 🚀"
echo "Starting your space exploration adventure..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.11+ to play Dockernauts"
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Error: Poetry is not installed"
    echo "Please install Poetry from https://python-poetry.org/docs/"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker from https://www.docker.com/"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Error: Docker Compose is not available"
    echo "Please install Docker Compose or use a newer version of Docker"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] || [ ! -f "compose.yaml" ]; then
    echo "❌ Error: Please run this script from the Dockernauts root directory"
    exit 1
fi

# Install dependencies if needed
if [ ! -d ".venv" ] && [ ! -f "poetry.lock" ]; then
    echo "📦 Installing dependencies..."
    poetry install
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to install dependencies"
        exit 1
    fi
fi

# Start Docker services
echo "🐳 Starting game services (Docker containers)..."
if command -v docker-compose &> /dev/null; then
    docker-compose up --build -d
else
    docker compose up --build -d
fi

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to start Docker services"
    echo "Make sure Docker is running and you have the necessary permissions"
    exit 1
fi

echo "✅ Docker services started successfully"

# Give services a moment to start up
echo "⏳ Waiting for services to initialize..."
sleep 3

# Start the game
echo "🎮 Launching Dockernauts..."
echo "Use Q to quit the game"
echo ""

# Function to cleanup Docker services on exit
cleanup() {
    echo ""
    echo "🧹 Cleaning up Docker services..."
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    else
        docker compose down
    fi
}

# Set trap to cleanup on script exit
trap cleanup EXIT

poetry run python src/main.py

echo ""
echo "👋 Thanks for playing Dockernauts!"