import asyncio
import os
from utils.nats import JetStreamClient
from utils.logger import Logger

from nats.aio.client import Client as NATS
from nats.js.api import StreamConfig
from nats.aio.msg import Msg

logger = Logger("master_station")
NATS_ADDRESS = os.getenv("NATS_ADDRESS", "nats://localhost:4222")

class MasterStation():
    def __init__(self):
        self.resources = {"gold": 0, "food": 0, "metal": 0}

    async def resource_cb(self, msg: dict):
        for k,v in msg.items():
            self.resources[k] += v

async def create_streams(streams: list):
    nc = NATS()
    await nc.connect(NATS_ADDRESS)

    js = nc.jetstream()

    for stream in streams:
        config = StreamConfig(
            name=stream,
            subjects=["{stream}.>"],
        )

        try:
            await js.add_stream(config)
        except Exception as e:
            logger.error(f"Failed to add stream: {e}")
    await nc.drain()

async def create_master_listener(master_station: MasterStation):
    master_listener = JetStreamClient(NATS_ADDRESS, "MASTER", "resources")
    master_listener.connect()
    master_listener.subscribe_json(master_station.resource_cb)

async def main():
    STREAMS = ["PLANETS", "MASTER"]
    master_station = MasterStation()
    create_streams(STREAMS)
    create_master_listener(master_station) 

if __name__ == "__main__":
    asyncio.run(main())
