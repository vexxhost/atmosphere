import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from atmosphere import config, deploy, logger
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
        deploy.run()


def main():
    LOG.info("Starting Atmosphere operator")

    deploy.run()
    LOG.info("Atmosphere operator successfully started")

    observer = Observer()
    observer.schedule(AtmosphereFileSystemEventHandler(), config.CONFIG_FILE)

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

    LOG.info("Stopping Atmosphere operator")
