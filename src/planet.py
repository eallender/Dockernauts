import asyncio
import json
import random
import time
from enum import Enum
from typing import Dict, Optional

from utils.logger import Logger
from utils.nats import NatsClient


class PlanetSize(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class Planet:
    def __init__(
        self, name, uuid, x=0, y=0, nats_address: str = "nats://localhost:4222"
    ):
        PLANET_SIZE_WEIGHTS = [0.4, 0.4, 0.2]  # Small: 40%, Medium: 40% Large: 20%
        self.name = name
        self.uuid = uuid
        self.x = x  # World coordinates for distance calculation
        self.y = y
        self.discovered = False
        self.claimed = False
        self.size = random.choices(list(PlanetSize), weights=PLANET_SIZE_WEIGHTS, k=1)[
            0
        ]
        self.available_resources = self._generate_resources(self.size)
        self.resource_collection_speed = {"food": 1, "gold": 1, "metal": 1}
        self.upgrade_levels = {"food": 0, "gold": 0, "metal": 0}

        self.nats_address = nats_address
        self.logger = Logger(f"Planet-{self.name}").get_logger()
        self.resource_publisher: Optional[NatsClient] = None
        self.upgrade_subscriber: Optional[NatsClient] = None

        self.running = False
        self.last_collection_time = time.time()

    async def start_processing(self):
        """Start the planet processing system"""
        if self.running:
            self.logger.warning(f"Planet {self.name} is already running")
            return

        self.running = True
        self.logger.info(f"Starting planet {self.name} processing")

        await self._setup_nats_connections()

        # Start resource collection and upgrade listening
        collection_task = asyncio.create_task(self._resource_collection_loop())

        try:
            await collection_task
        except Exception as e:
            self.logger.error(f"Error in planet processing: {e}")
        finally:
            await self.stop_processing()

    async def stop_processing(self):
        """Stop the planet processing system"""
        self.running = False
        self.logger.info(f"Stopping planet {self.name} processing")

        if self.resource_publisher:
            await self.resource_publisher.close()
        if self.upgrade_subscriber:
            await self.upgrade_subscriber.close()

    async def _setup_nats_connections(self):
        """Setup NATS connections for communication"""
        self.resource_publisher = NatsClient(self.nats_address, "MASTER.resources")
        await self.resource_publisher.connect()

        self.upgrade_subscriber = NatsClient(
            self.nats_address, f"PLANETS.{self.uuid}.upgrades"
        )
        await self.upgrade_subscriber.connect()
        await self.upgrade_subscriber.subscribe_js(self._handle_upgrade_command)

    async def _resource_collection_loop(self):
        """Main resource collection loop"""
        while self.running:
            try:
                current_time = time.time()
                time_diff = current_time - self.last_collection_time

                if time_diff >= 1.0:  # Collect every second
                    collected_resources = self._collect_resources(time_diff)

                    if any(collected_resources.values()):
                        await self._send_resources_to_master(collected_resources)
                        self.logger.debug(f"Sent resources: {collected_resources}")

                    self.last_collection_time = current_time

                await asyncio.sleep(0.1)  # Small sleep to prevent busy waiting

            except Exception as e:
                self.logger.error(f"Error in resource collection: {e}")
                await asyncio.sleep(1)

    def _collect_resources(self, time_diff: float) -> Dict[str, int]:
        """Collect resources based on collection speed and available resources"""
        collected = {"food": 0, "gold": 0, "metal": 0}

        for resource_type in ["food", "gold", "metal"]:
            if self.available_resources.get(resource_type, 0) > 0:
                # Calculate collection amount based on speed, upgrades, and time
                base_collection = self.resource_collection_speed.get(resource_type, 1)
                upgrade_multiplier = 1 + (
                    self.upgrade_levels.get(resource_type, 0) * 0.5
                )
                collection_amount = int(
                    base_collection * upgrade_multiplier * time_diff
                )

                # Don't collect more than available
                actual_collection = min(
                    collection_amount, self.available_resources[resource_type]
                )

                collected[resource_type] = actual_collection
                self.available_resources[resource_type] -= actual_collection

        return collected

    async def _send_resources_to_master(self, resources: Dict[str, int]):
        """Send collected resources to master station"""
        try:

            await self.resource_publisher.publish_js_json(resources)

        except Exception as e:
            self.logger.error(f"Failed to send resources to master: {e}")

    async def _handle_upgrade_command(self, msg):
        """Handle upgrade commands from the master station"""
        try:
            data = json.loads(msg.data.decode())
            resource_type = data.get("resource_type")
            upgrade_cost = data.get("cost", {})

            if resource_type in ["food", "gold", "metal"]:
                # Check if upgrade is possible (this would normally check master station resources)
                success = self._apply_upgrade(resource_type)

                if success:
                    self.logger.info(
                        f"Successfully upgraded {resource_type} production on {self.name}"
                    )
                else:
                    self.logger.warning(
                        f"Failed to upgrade {resource_type} production on {self.name}"
                    )

        except Exception as e:
            self.logger.error(f"Error handling upgrade command: {e}")

    def _apply_upgrade(self, resource_type: str) -> bool:
        """Apply an upgrade to resource production"""
        if resource_type in self.upgrade_levels:
            self.upgrade_levels[resource_type] += 1
            self.logger.info(
                f"Upgraded {resource_type} to level {self.upgrade_levels[resource_type]}"
            )
            return True
        return False

    def calculate_claim_cost(self) -> int:
        """Calculate the cost to claim this planet based on distance from origin (0,0)"""
        import math

        # Calculate distance from origin
        distance = math.sqrt(self.x**2 + self.y**2)

        # Base claim cost starts at 100 gold for planets at origin
        base_cost = 100

        # Cost increases with distance - every 100 units adds 50 gold
        # Plus size multiplier: small=1x, medium=1.5x, large=2x
        size_multiplier = {
            PlanetSize.SMALL: 1.0,
            PlanetSize.MEDIUM: 1.5,
            PlanetSize.LARGE: 2.0,
        }

        distance_cost = int(distance / 100) * 50
        total_cost = int((base_cost + distance_cost) * size_multiplier[self.size])

        return max(total_cost, base_cost)  # Minimum cost is base_cost

    def claim_planet(self, cost_paid: int) -> bool:
        """Attempt to claim the planet if sufficient cost is paid"""
        required_cost = self.calculate_claim_cost()

        if cost_paid >= required_cost and not self.claimed:
            self.claimed = True
            self.logger.info(f"Planet {self.name} claimed for {cost_paid} gold")
            return True

        return False

    def get_planet_status(self) -> Dict:
        """Get current planet status for UI display"""
        return {
            "name": self.name,
            "uuid": self.uuid,
            "size": self.size.value,
            "discovered": self.discovered,
            "claimed": self.claimed,
            "x": self.x,
            "y": self.y,
            "claim_cost": self.calculate_claim_cost(),
            "available_resources": self.available_resources.copy(),
            "collection_speed": self.resource_collection_speed.copy(),
            "upgrade_levels": self.upgrade_levels.copy(),
            "running": self.running,
        }

    @staticmethod
    def _generate_resources(size: PlanetSize) -> dict:
        SMALL_MIN_RESOURCES = 500
        MEDIUM_MIN_RESOURCES = 1000
        LARGE_MIN_RESOURCES = 1500
        LARGE_MAX_RESOURCES = 2000
        match size:
            case PlanetSize.SMALL:
                food = random.randint(SMALL_MIN_RESOURCES, MEDIUM_MIN_RESOURCES)
                gold = random.randint(SMALL_MIN_RESOURCES, MEDIUM_MIN_RESOURCES)
                metal = random.randint(SMALL_MIN_RESOURCES, MEDIUM_MIN_RESOURCES)
            case PlanetSize.MEDIUM:
                food = random.randint(MEDIUM_MIN_RESOURCES, LARGE_MIN_RESOURCES)
                gold = random.randint(MEDIUM_MIN_RESOURCES, LARGE_MIN_RESOURCES)
                metal = random.randint(MEDIUM_MIN_RESOURCES, LARGE_MIN_RESOURCES)
            case PlanetSize.LARGE:
                food = random.randint(LARGE_MIN_RESOURCES, LARGE_MAX_RESOURCES)
                gold = random.randint(LARGE_MIN_RESOURCES, LARGE_MAX_RESOURCES)
                metal = random.randint(LARGE_MIN_RESOURCES, LARGE_MAX_RESOURCES)
        return {
            "food": food,
            "gold": gold,
            "metal": metal,
        }


async def main():
    """Main function to run a planet processor standalone"""
    import os
    import sys

    if len(sys.argv) < 3:
        print("Usage: python planet.py <planet_name> <planet_uuid> [nats_address]")
        sys.exit(1)

    planet_name = sys.argv[1]
    planet_uuid = sys.argv[2]
    nats_address = (
        sys.argv[3]
        if len(sys.argv) > 3
        else os.getenv("NATS_ADDRESS", "nats://localhost:4222")
    )

    # Create a new planet
    planet = Planet(planet_name, planet_uuid, nats_address)

    print(f"Starting planet processor for {planet_name} ({planet_uuid})")
    print(f"Planet size: {planet.size.value}")
    print(f"Initial resources: {planet.available_resources}")

    try:
        await planet.start_processing()
    except KeyboardInterrupt:
        print(f"\nShutting down planet {planet_name}")
        await planet.stop_processing()


if __name__ == "__main__":
    asyncio.run(main())
