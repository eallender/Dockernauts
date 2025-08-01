import argparse
import asyncio

from nats.aio.client import Client as NATS


async def main():
    parser = argparse.ArgumentParser(description="JetStream Publisher")
    parser.add_argument("subject", help="Subject to publish to")
    parser.add_argument("payload", help="Payload message")
    parser.add_argument(
        "--nats-url", default="nats://localhost:4222", help="NATS server URL"
    )
    args = parser.parse_args()

    nc = NATS()
    await nc.connect(servers=[args.nats_url])

    js = nc.jetstream()

    ack = await js.publish(args.subject, args.payload.encode())
    print(
        f"✅ Published to '{args.subject}' with sequence {ack.seq} in stream '{ack.stream}'"
    )

    await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())
