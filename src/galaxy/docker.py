import docker
from utils.logger import Logger

client = docker.from_env()
logger = Logger("docker_manager")

def start_container(image_name, container_name, ports=None, environment=None):
    try:
        container = client.containers.run(
            image=image_name,
            name=container_name,
            ports=ports,
            environment=environment,
            detach=True
        )
        logger.info(f" Started container: {container_name}")
        return container
    except docker.errors.APIError as e:
        logger.error(f"Failed to start container '{container_name}': {e.explanation}")

def stop_container(container_name):
    try:
        container = client.containers.get(container_name)
        container.stop()
        logger.info(f"Stopped container: {container_name}")
    except docker.errors.NotFound:
        logger.error(f"No container found with name '{container_name}'")
    except docker.errors.APIError as e:
        logger.error(f"Error stopping container '{container_name}': {e.explanation}")