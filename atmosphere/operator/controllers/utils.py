import kopf
import pykube
from oslo_serialization import base64


def get_or_wait_for_secret(
    api: pykube.HTTPClient, namespace: str, name: str, delay: int = 5
) -> pykube.Secret:
    secret = pykube.Secret.objects(api, namespace=namespace).get_or_none(name=name)
    if secret is None:
        raise kopf.TemporaryError(
            f"secret/{name} in {namespace} is not yet ready.", delay=delay
        )
    return {k: base64.decode_as_text(v) for k, v in secret.obj["data"].items()}
