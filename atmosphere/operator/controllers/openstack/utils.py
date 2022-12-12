from importlib.metadata import version

import openstack
import openstack.connection
import pykube

from atmosphere import clients
from atmosphere.operator.controllers import utils


def get_client(
    namespace: str, api: pykube.HTTPClient = None
) -> openstack.connection.Connection:
    if api is None:
        api = clients.get_pykube_api()

    secret = utils.get_or_wait_for_secret(api, namespace, "keystone-keystone-admin")
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
        app_version=version("atmosphere"),
    )
