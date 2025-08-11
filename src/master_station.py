import asyncio
import json
import os
import time

from utils.logger import Logger
from utils.nats import NatsClient

NATS_ADDRESS = os.getenv("NATS_ADDRESS", "nats://localhost:4222")
NATS_STREAMS = ["PLANETS", "MASTER"]


class MasterStation:
    def __init__(self):
        self.resources = {"gold": 250, "food": 250, "metal": 250}
        self.logger = Logger(__name__).get_logger()
        self.game_state_publisher = None  # track it for reuse
        self.game_reset_subscriber = None
        self.base_food_consumption_rate = 1
        self.game_start_time = time.time()
        self.food_consumption_timer = None

    async def resource_cb(self, msg):
        try:
            self.logger.debug("Received resource transmission")
            data = json.loads(msg.data.decode())
            for k, v in data.items():
                new_value = self.resources[k] + int(v)
                # Prevent resources from going negative
                self.resources[k] = max(0, new_value)
            self.logger.debug(
                f"Gold: {self.resources.get('gold')}, Food: {self.resources.get('food')}, Metal: {self.resources.get('metal')}"
            )
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in message: {msg.data} — {e}")
        except Exception as e:
            self.logger.exception(f"Error handling resource message: {e}")

    async def game_state_reply_cb(self, msg, publisher):
        try:
            game_stats = {
                "resources": self.resources,
            }
            await publisher.publish_reply_json(game_stats, msg)
        except Exception as e:
            self.logger.exception(f"Failed to handle game state request: {e}")

    async def create_master_subs(self):
        self.master_resource_sub = NatsClient(NATS_ADDRESS, "MASTER.resources")
        await self.master_resource_sub.connect()
        await self.master_resource_sub.create_streams(NATS_STREAMS)
        # Purge old messages to prevent startup flooding
        await self.master_resource_sub.purge_stream_messages("MASTER")
        await self.master_resource_sub.subscribe_js(self.resource_cb)

    async def create_game_state_pub(self):
        self.game_state_publisher = NatsClient(NATS_ADDRESS, "game.state")
        await self.game_state_publisher.connect()

        async def callback_wrapper(msg):
            await self.game_state_reply_cb(msg, self.game_state_publisher)

        await self.game_state_publisher.subscribe(callback_wrapper)

    async def consume_food(self):
        """Consume food for survival mechanics with progressive scaling"""
        # Calculate current consumption rate (increases every 30 seconds)
        time_elapsed = time.time() - self.game_start_time
        scaling_factor = 1 + (time_elapsed // 30) * 0.5  # +0.5 every 30 seconds
        current_consumption = int(self.base_food_consumption_rate * scaling_factor)

        if self.resources["food"] > 0:
            self.resources["food"] = max(
                0, self.resources["food"] - current_consumption
            )
            self.logger.info(
                f"Food consumed: {current_consumption}, Remaining: {self.resources['food']}"
            )
        else:
            self.logger.warning("No food remaining! Survival at risk.")

    async def start_food_consumption_timer(self):
        """Start the food consumption timer"""
        if self.food_consumption_timer is None:
            self.food_consumption_timer = asyncio.create_task(
                self._food_consumption_loop()
            )

    async def _food_consumption_loop(self):
        """Background loop for food consumption"""
        while True:
            await asyncio.sleep(1)  # Check every second
            await self.consume_food()

    async def reset_game_state(self):
        """Reset the game state for a new game"""
        self.resources = {"gold": 200, "food": 200, "metal": 200}
        self.game_start_time = time.time()
        self.logger.info("Game state reset - starting with 200 of each resource")

    async def game_reset_cb(self, msg):
        """Handle game reset messages"""
        try:
            await self.reset_game_state()
            self.logger.info("Game reset completed")
        except Exception as e:
            self.logger.exception(f"Error during game reset: {e}")

    async def create_game_reset_sub(self):
        """Create subscriber for game reset messages"""
        self.game_reset_subscriber = NatsClient(NATS_ADDRESS, "game.reset")
        await self.game_reset_subscriber.connect()
        await self.game_reset_subscriber.subscribe(self.game_reset_cb)


async def main():
    master_station = MasterStation()
    await master_station.create_master_subs()
    await master_station.create_game_state_pub()
    await master_station.create_game_reset_sub()
    await master_station.start_food_consumption_timer()

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
