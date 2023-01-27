import logging

import kopf
from taskflow import engines
from taskflow.listeners import logging as logging_listener
from taskflow.patterns import graph_flow

from atmosphere import clients, flows
from atmosphere.models import config
from atmosphere.operator.api import Cloud


@kopf.on.resume(Cloud.version, Cloud.kind)
@kopf.on.create(Cloud.version, Cloud.kind)
def create_fn(namespace: str, name: str, spec: dict, **_):
    api = clients.get_pykube_api()

    # TODO(mnaser): Get rid of this flow.
    cfg = config.Config.from_file()
    engine = flows.get_engine(cfg)
    engine.run()

    flow = graph_flow.Flow("deploy")

    engine = engines.load(
        flow,
        store={
            "api": api,
            "namespace": namespace,
            "name": name,
            "spec": spec,
        },
        executor="greenthreaded",
        engine="parallel",
        max_workers=4,
    )

    with logging_listener.DynamicLoggingListener(engine, level=logging.INFO):
        engine.run()
