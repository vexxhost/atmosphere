import kopf

from atmosphere import flows
from atmosphere.models import config
from atmosphere.operator.api import Cloud


@kopf.on.resume(Cloud.version, Cloud.kind)
@kopf.on.create(Cloud.version, Cloud.kind)
def create_fn(namespace: str, name: str, spec: dict, **_):
    # TODO(mnaser): Get rid of this flow.
    cfg = config.Config.from_file()
    engine = flows.get_engine(cfg)
    engine.run()
