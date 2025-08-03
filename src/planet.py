import random
from enum import Enum

# from utils.nats import JetStreamClient


class PlanetSize(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class Planet:
    def __init__(self, name, uuid):
        PLANET_SIZE_WEIGHTS = [0.4, 0.4, 0.2]  # Small: 40%, Medium: 40% Large: 20%
        self.name = name
        self.uuid = uuid
        self.discovered = False
        self.claimed = False
        self.size = random.choices(list(PlanetSize), weights=PLANET_SIZE_WEIGHTS, k=1)[
            0
        ]
        self.available_resources = self.__generate_resources()
        self.resource_collection_speed = {"food": 1, "gold": 1, "metal": 1}

    # def __start_upgrade_listener(self):
    #     NATS_ADDRESS = "nats://127.0.0.1:4222" #TODO will need to change for network
    #     STREAM = "PLANETS"
    #     upgrade_listener = JetStreamClient(NATS_ADDRESS, stream_name=STREAM, subject=self.uuid)
    #     upgrade_listener.connect()

    # def __start_resource_collectors():

    def __generate_resources(self) -> dict:
        SMALL_MIN_RESOURCES = 500
        MEDIUM_MIN_RESOURCES = 1000
        LARGE_MIN_RESOURCES = 1500
        LARGE_MAX_RESOURCES = 2000
        match self.size:
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
