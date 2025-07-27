import json
from utils.logger import Logger
from nats.aio.client import Client as NATS

class JetStreamClient:
    def __init__(self, servers="nats://localhost:4222", stream_name="mystream", subject="updates"):
        self.servers = servers
        self.stream_name = stream_name
        self.subject = subject
        self.nc = NATS()
        self.js = None
        self.logger = Logger("nats_logger")

    async def connect(self):
        await self.nc.connect(servers=[self.servers])
        self.js = self.nc.jetstream()

    async def publish_json(self, data: dict):
        message = json.dumps(data)
        ack = await self.js.publish(self.subject, message.encode())
        self.logger.debug(f"Published to {self.subject}, seq={ack.seq}")

    async def subscribe_json(self, callback):
        async def message_handler(msg):
            try:
                decoded = json.loads(msg.data.decode())
                await callback(decoded)
            except json.JSONDecodeError:
                self.logger.error(f"Invalid JSON: {msg.data}")

        await self.js.subscribe(self.subject, cb=message_handler, durable="durable")

    async def close(self):
        await self.nc.close()