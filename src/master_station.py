import asyncio
import json
import os

from utils.logger import Logger
from utils.nats import NatsClient

NATS_ADDRESS = os.getenv("NATS_ADDRESS", "nats://localhost:4222")
NATS_STREAMS = ["PLANETS", "MASTER"]


class MasterStation:
    def __init__(self):
        self.resources = {"gold": 0, "food": 0, "metal": 0}
        self.logger = Logger(__name__).get_logger()
        self.game_state_publisher = None  # track it for reuse

    async def resource_cb(self, msg):
        try:
            self.logger.debug("Received resource transmission")
            data = json.loads(msg.data.decode())
            for k, v in data.items():
                self.resources[k] += int(v)
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
        await self.master_resource_sub.subscribe_js(self.resource_cb)

    async def create_game_state_pub(self):
        self.game_state_publisher = NatsClient(NATS_ADDRESS, "game.state")
        await self.game_state_publisher.connect()

        async def callback_wrapper(msg):
            await self.game_state_reply_cb(msg, self.game_state_publisher)

        await self.game_state_publisher.subscribe(callback_wrapper)


async def main():
    master_station = MasterStation()
    await master_station.create_master_subs()
    await master_station.create_game_state_pub()

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
