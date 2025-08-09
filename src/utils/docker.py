import asyncio
import threading

import docker
from utils.logger import Logger

logger = Logger(__name__).get_logger()

# Initialize Docker client with error handling
try:
    client = docker.from_env()
    # Test the connection
    client.ping()
    logger.info("Docker connection established successfully")
except docker.errors.DockerException as e:
    logger.error(f"Failed to connect to Docker daemon: {e}")
    logger.error("Please make sure Docker is running and accessible")
    client = None
except Exception as e:
    logger.error(f"Unexpected error connecting to Docker: {e}")
    client = None


def remove_container(container_name):
    if client is None:
        logger.error(
            f"Cannot remove container '{container_name}': Docker client not available"
        )
        return

    try:
        container = client.containers.get(container_name)
        container.stop()
        container.remove()
        logger.info(f"Stopped and removed container: {container_name}")
    except docker.errors.NotFound:
        logger.error(f"No container found with name '{container_name}'")
    except docker.errors.APIError as e:
        logger.error(f"Error removing container '{container_name}': {e.explanation}")


def start_planet_container(
    planet_name, planet_uuid, nats_address="nats://localhost:4222"
):
    """Start a Docker container for a planet with the planet processor using the custom planet image"""
    if client is None:
        logger.error(f"Cannot start planet container: Docker client not available")
        return None

    container_name = f"planet-{planet_uuid}"

    try:
        container = client.containers.run(
            image="dockernauts-planet:latest",
            name=container_name,
            command=[planet_name, planet_uuid, nats_address],
            environment={"NATS_ADDRESS": nats_address},
            network_mode="host",  # Use host network to access NATS
            detach=True,
            restart_policy={"Name": "unless-stopped"},
        )
        logger.info(
            f"Started planet container: {container_name} for planet {planet_name}"
        )
        return container
    except docker.errors.ImageNotFound:
        logger.error(
            f"Planet image 'dockernauts-planet:latest' not found. Please build it with: docker compose build build-planet-image"
        )
        return None
    except docker.errors.APIError as e:
        logger.error(
            f"Failed to start planet container '{container_name}': {e.explanation}"
        )
        return None


def _cleanup_containers_sync():
    """Synchronous cleanup helper - runs in background thread"""
    if client is None:
        logger.error("Cannot cleanup planet containers: Docker client not available")
        return

    try:
        logger.info(f"Starting container clean up process...")
        # Get all containers with names starting with "planet-"
        containers = client.containers.list(all=True, filters={"name": "planet-"})

        removed_count = 0
        for container in containers:
            try:
                logger.info(f"Removing planet container: {container.name}")
                container.stop()
                container.remove()
                removed_count += 1
            except Exception as e:
                logger.error(f"Failed to remove container {container.name}: {e}")

        if removed_count > 0:
            logger.info(f"Successfully removed {removed_count} planet containers")
        else:
            logger.info("No planet containers found to remove")

    except docker.errors.APIError as e:
        logger.error(f"Error during planet container cleanup: {e.explanation}")


def cleanup_non_home_planet_containers():
    """Remove all planet containers except home-planet for game reset"""
    if client is None:
        logger.error("Cannot cleanup planet containers: Docker client not available")
        return

    try:
        logger.info("Starting cleanup of non-home planet containers...")
        # Get all planet containers (both "planet-{uuid}" and "dockernauts-planet-home")
        all_containers = client.containers.list(all=True)
        containers = [c for c in all_containers if "planet" in c.name]

        removed_count = 0
        for container in containers:
            # Skip the home-planet container (dockernauts-planet-home)
            if container.name == "dockernauts-planet-home":
                logger.info(f"Skipping home planet container: {container.name}")
                continue
                
            try:
                logger.info(f"Removing planet container: {container.name}")
                container.stop()
                container.remove()
                removed_count += 1
            except Exception as e:
                logger.error(f"Failed to remove container {container.name}: {e}")

        if removed_count > 0:
            logger.info(f"Successfully removed {removed_count} non-home planet containers")
        else:
            logger.info("No non-home planet containers found to remove")

    except docker.errors.APIError as e:
        logger.error(f"Error during planet container cleanup: {e.explanation}")


def cleanup_all_planet_containers():
    """Remove all planet containers when the game exits - runs in background"""
    logger.info("Starting background cleanup of planet containers")

    def run_cleanup():
        # Show user notification about cleanup (after UI closes)
        print("\n🧹 Cleaning up planet containers in the background...")
        print("💫 Container cleanup will continue - you can safely close this terminal")

        _cleanup_containers_sync()

        logger.info("Background cleanup completed")

        # Final user notification
        print("✅ Planet container cleanup completed")

    # Start cleanup in background thread (non-daemon so it can complete)
    cleanup_thread = threading.Thread(target=run_cleanup, daemon=False)
    cleanup_thread.start()
    logger.info("Background cleanup thread started - game will exit immediately")
