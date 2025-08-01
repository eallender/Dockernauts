import asyncio
import json

from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrNoServers, ErrTimeout

from utils.logger import Logger


class JetStreamClient:
    def __init__(self, servers, subject, max_retries=5, retry_delay=2):
        self.servers = servers
        self.subject = subject
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.nc = NATS()
        self.js = None
        self.logger = Logger(__name__).get_logger()

    async def connect(self):
        try:
            await self.nc.connect(
                servers=[self.servers],
                disconnected_cb=self.on_disconnect,
                reconnected_cb=self.on_reconnect,
                closed_cb=self.on_close,
                error_cb=self.on_error,
                connect_timeout=2,
                max_reconnect_attempts=self.max_retries,
                reconnect_time_wait=self.retry_delay,
            )
            self.js = self.nc.jetstream()
            self.logger.info(f"Connected to NATS at {self.servers}")
        except ErrNoServers as e:
            self.logger.error(f"Could not connect to NATS server: {e}")

    async def on_disconnect(self, nc):
        self.logger.warning("Disconnected from NATS.")

    async def on_reconnect(self, nc):
        self.logger.info("Reconnected to NATS.")

    async def on_close(self, nc):
        self.logger.warning("Connection to NATS closed.")

    async def on_error(self, nc, sub, error):
        self.logger.error(f"NATS error on subscription '{sub}': {error}")

    async def publish_json(self, data: dict):
        if not self.js:
            self.logger.error("Cannot publish: not connected to JetStream.")
            return
        try:
            message = json.dumps(data)
            ack = await self.js.publish(self.subject, message.encode())
            self.logger.debug(
                f"Published to '{self.subject}', seq={ack.seq}, stream={ack.stream}"
            )
        except Exception as e:
            self.logger.exception(f"Failed to publish message: {e}")

    async def subscribe_json(self, callback):
        if not self.js:
            self.logger.error("Cannot subscribe: not connected to JetStream.")
            return

        async def message_handler(msg):
            try:
                decoded = json.loads(msg.data.decode())
                self.logger.debug(f"Received message on '{msg.subject}': {decoded}")
                await callback(decoded)
            except json.JSONDecodeError:
                self.logger.error(f"Invalid JSON received: {msg.data}")

        try:
            await self.js.subscribe(self.subject, cb=message_handler, durable="durable")
            self.logger.info(f"Subscribed to '{self.subject}' with durable consumer.")
        except Exception as e:
            self.logger.exception(f"Failed to subscribe: {e}")

    async def close(self):
        if self.nc.is_connected:
            self.logger.info("Closing NATS connection...")
            await self.nc.drain()
            await self.nc.close()
            self.logger.info("NATS connection closed.")
