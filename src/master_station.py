import asyncio
import os

from nats.aio.client import Client as NATS
from nats.aio.msg import Msg
from nats.js.api import StreamConfig
from nats.js.errors import NotFoundError

from utils.logger import Logger
from utils.nats import JetStreamClient

NATS_ADDRESS = os.getenv("NATS_ADDRESS", "nats://localhost:4222")
NATS_STREAMS = ["PLANETS", "MASTER"]


class MasterStation:
    def __init__(self):
        self.resources = {"gold": 0, "food": 0, "metal": 0}
        self.logger = Logger(__name__).get_logger()
        self.nc = NATS()

    async def resource_cb(self, msg: dict):
        for k, v in msg.items():
            self.resources[k] += v

    async def create_streams(self, streams: list):
        if self.nc.is_connected:
            js = self.nc.jetstream()

            for stream in streams:
                try:
                    await js.stream_info(stream)
                    self.logger.debug(f"NATs stream, {stream}, already exists")
                except NotFoundError:
                    config = StreamConfig(
                        name=stream,
                        subjects=["{stream}.>"],
                    )
                    try:
                        await js.add_stream(config)
                        self.logger.debug(f"Added NATs stream: {stream}")
                    except Exception as e:
                        self.logger.error(f"Failed to add stream: {e}")
            await self.nc.drain()

    async def create_master_listener(self):
        self.master_listener = JetStreamClient(NATS_ADDRESS, "MASTER", "resources")
        await self.master_listener.connect()
        await self.master_listener.subscribe_json(self.resource_cb)


async def main():
    master_station = MasterStation()
    await master_station.create_streams(NATS_STREAMS)
    await master_station.create_master_listener()


if __name__ == "__main__":
    asyncio.run(main())
