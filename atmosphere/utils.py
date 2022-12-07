import json

import _jsonnet
import kopf
import openstack
import pykube
from oslo_serialization import base64

from atmosphere import clients


def load_jsonnet_from_path(path: str) -> any:
    raw = _jsonnet.evaluate_file(path)
    return json.loads(raw)


def get_or_wait_for_secret(
    api: pykube.HTTPClient, namespace: str, name: str, delay: int = 5
) -> pykube.Secret:
    secret = pykube.Secret.objects(api, namespace=namespace).get_or_none(name=name)
    if secret is None:
        raise kopf.TemporaryError(
            f"secret/{name} in {namespace} is not yet ready.", delay=delay
        )
    return {k: base64.decode_as_text(v) for k, v in secret.obj["data"].items()}


def get_openstack_client(
    namespace: str, api: pykube.HTTPClient = None
) -> openstack.connection.Connection:
    if api is None:
        api = clients.get_pykube_api()

    secret = get_or_wait_for_secret(api, namespace, "keystone-keystone-admin")
    return openstack.connect(
        auth_url=secret["OS_AUTH_URL"],
        interface="internal",
        project_name=secret["OS_PROJECT_NAME"],
        username=secret["OS_USERNAME"],
        password=secret["OS_PASSWORD"],
        region_name=secret["OS_REGION_NAME"],
        user_domain_name=secret["OS_USER_DOMAIN_NAME"],
        project_domain_name=secret["OS_PROJECT_DOMAIN_NAME"],
        app_name="atmosphere",
        app_version="TODO",
    )
