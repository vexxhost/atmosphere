import click
import pykube

from atmosphere import deploy
from atmosphere.models import conf


@click.command()
@click.option("--config", help="Path to Atmosphere config file", required=True)
def run(config):
    config = conf.from_file(config)

    kube_config = pykube.KubeConfig.from_env()
    api = pykube.HTTPClient(kube_config)

    deploy.run(api, config)


if __name__ == "__main__":
    run()
