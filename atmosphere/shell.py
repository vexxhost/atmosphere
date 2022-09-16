import click
import pykube

from atmosphere.models import conf
from atmosphere import deploy


@click.command()
@click.option("--config", help="Path to Atmosphere config file", required=True)
def deploy(config):
    config = conf.from_file(config)

    kube_config = pykube.KubeConfig.from_env()
    api = pykube.HTTPClient(kube_config)

    deploy.run(api, config)


if __name__ == "__main__":
    deploy()
