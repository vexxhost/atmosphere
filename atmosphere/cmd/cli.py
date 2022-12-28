import shutil

import click
from oslo_concurrency import processutils
from oslo_config import cfg
from oslo_log import log as logging

from atmosphere.operator import constants, utils

CONF = cfg.CONF
LOG = logging.getLogger(__name__)
DOMAIN = "atmosphere"

logging.register_options(CONF)
logging.setup(CONF, DOMAIN)


@click.group()
def main():
    pass


@main.group()
def image():
    pass


@image.command()
@click.argument("destination")
def mirror(destination):
    crane_path = shutil.which("crane")

    if crane_path is None:
        raise click.UsageError(
            "Crane is not installed. Please install it before running this command."
        )

    seen = []
    for image in constants.IMAGE_LIST:
        if constants.IMAGE_LIST[image] in seen:
            continue

        src = constants.IMAGE_LIST[image]
        dst = utils.get_image_ref(image, override_registry=destination).string()

        LOG.debug(f"Starting to mirror {src} to {dst}")

        try:
            processutils.execute(
                crane_path,
                "copy",
                src,
                dst,
            )
        except processutils.ProcessExecutionError as e:
            if "401 Unauthorized" in e.stderr:
                LOG.error(
                    "Authentication failed. Please ensure you're logged in via Crane"
                )
                return

            raise

        seen.append(constants.IMAGE_LIST[image])
        LOG.info(f"Successfully mirrored {src} to {dst}")
