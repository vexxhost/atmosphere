import time

from atmosphere import flows, logger
from atmosphere.models import config

LOG = logger.get_logger()


def main():
    LOG.info("Starting Atmosphere operator")

    cfg = config.Config.from_file()

    engine = flows.get_engine(cfg)
    engine.run()
    LOG.info("Atmosphere operator successfully started")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    LOG.info("Stopping Atmosphere operator")
