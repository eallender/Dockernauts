import argparse
import asyncio
import json

from nats.aio.client import Client as NATS


async def main():
    parser = argparse.ArgumentParser(description="JetStream Publisher")
    parser.add_argument("--food", default="0", help="Food to give to the player")
    parser.add_argument("--metal", default="0", help="Metal to give to the player")
    parser.add_argument("--gold", default="0", help="Gold to give to the player")
    parser.add_argument(
        "--nats-url", default="nats://localhost:4222", help="NATS server URL"
    )
    parser.add_argument("--subject", default="MASTER.resources", help="NATS subject")
    args = parser.parse_args()

    nc = NATS()
    await nc.connect(servers=[args.nats_url])
    js = nc.jetstream()

    resources = {
        "food": int(args.food),
        "metal": int(args.metal),
        "gold": int(args.gold),
    }

    payload = json.dumps(resources).encode()
    ack = await js.publish(args.subject, payload)
    print(
        f"✅ Published to '{args.subject}' with sequence {ack.seq} in stream '{ack.stream}'"
    )

    await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())
