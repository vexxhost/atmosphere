import time

import taskflow.engines
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from atmosphere import config, flows, logger
from atmosphere.config import CONF

LOG = logger.get_logger()


class AtmosphereFileSystemEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        LOG.info("Detected change in config file, reloading")
        # NOTE(mnaser): Honestly, after two days, I have no idea why overriding
        #               the CONF object directly doesn't work, instead we override
        #               all of it's attribute one by one and.. that works.
        conf = config.load_config(event.src_path)
        for c in config._root_config:
            group = conf.get(c.name)
            setattr(CONF, c.name, group)
        engine = taskflow.engines.load(flows.get_deployment_flow())
        engine.run()


def main():
    LOG.info("Starting Atmosphere operator")

    engine = taskflow.engines.load(flows.get_deployment_flow())
    engine.run()
    LOG.info("Atmosphere operator successfully started")

    observer = Observer()
    observer.schedule(
        AtmosphereFileSystemEventHandler(), config.CONFIG_FILE, recursive=True
    )

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

    LOG.info("Stopping Atmosphere operator")
