import os

import kopf

from atmosphere import flows
from atmosphere.models import config
from atmosphere.operator import controllers  # noqa: F401


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.admission.server = kopf.WebhookServer(host=os.environ["POD_IP"])
    settings.admission.managed = "auto.atmosphere.vexxhost.com"


@kopf.on.startup()
def startup(**_):
    cfg = config.Config.from_file()
    engine = flows.get_engine(cfg)
    engine.run()
