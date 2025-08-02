import asyncio
import json

from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrNoServers, ErrTimeout
from nats.aio.msg import Msg
from nats.js.api import StreamConfig
from nats.js.errors import NotFoundError

from utils.logger import Logger


class NatsClient:
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

    async def publish_js_json(self, data: dict):
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

    async def publish_reply_json(self, data: dict, msg: Msg):
        if not self.nc:
            self.logger.error("Cannot publish: not connected to NATs.")
            return
        try:
            ack = await self.nc.publish(msg.reply, json.dumps(data).encode())
            self.logger.debug(f"Published to '{self.subject}'")
        except Exception as e:
            self.logger.exception(f"Failed to publish message: {e}")

    async def subscribe_js(self, callback, *callback_args):
        if not self.js:
            self.logger.error("Cannot subscribe: not connected to JetStream.")
            return

        try:
            await self.js.subscribe(self.subject, cb=callback)
            self.logger.debug(f"Subscribed to '{self.subject}'")
        except Exception as e:
            self.logger.exception(f"Failed to subscribe: {e}")

    async def subscribe(self, callback, *callback_args):
        if not self.nc.is_connected:
            self.logger.error(
                f"Cannot subscribe to {self.subject}: not connected to NATS."
            )
            return
        try:
            await self.nc.subscribe(self.subject, cb=callback)
            self.logger.debug(f"Subscribed to subject '{self.subject}'")
        except Exception as e:
            self.logger.exception(f"Failed to subscribe: {e}")

    async def create_streams(self, streams: list):
        if not self.nc.is_connected:
            await self.nc.connect(servers=[self.servers])

        js = self.nc.jetstream()

        for stream in streams:
            try:
                await js.stream_info(stream)
                self.logger.debug(f"NATS stream '{stream}' already exists")
            except NotFoundError:
                config = StreamConfig(
                    name=stream,
                    subjects=[f"{stream}.>"],
                )
                try:
                    await js.add_stream(config)
                    self.logger.debug(f"Added NATS stream: '{stream}'")
                except Exception as e:
                    self.logger.error(f"Failed to add stream '{stream}': {e}")

    async def on_disconnect(self, nc):
        self.logger.warning("Disconnected from NATS.")

    async def on_reconnect(self, nc):
        self.logger.info("Reconnected to NATS.")

    async def on_close(self, nc):
        self.logger.warning("Connection to NATS closed.")

    async def on_error(self, error):
        self.logger.error(f"A NATS error occurred: {error}")

    async def close(self):
        if self.nc.is_connected:
            self.logger.info("Closing NATS connection...")
            await self.nc.drain()
            await self.nc.close()
            self.logger.info("NATS connection closed.")
