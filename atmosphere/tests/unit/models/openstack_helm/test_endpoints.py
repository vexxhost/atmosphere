import pytest
import requests
import yaml

from atmosphere.config import CONF
from atmosphere.models.openstack_helm import endpoints as osh_endpoints

# XXX(mnaser): Once we have the details of our charts codified, we can get rid
#              of this.
CHART_LOOKUP_TABLE = {
    "memcached": "openstack-helm-infra",
}


@pytest.mark.parametrize(
    "project,chart",
    [(CHART_LOOKUP_TABLE[c], c) for c in osh_endpoints.Endpoints.ENDPOINTS],
)
def test_openstack_helm_endpoint_keys(project, chart):
    ignored_keys = [
        "cluster_domain_suffix",
        "local_image_registry",
        "oci_image_registry",
        "kube_dns",
    ]

    raw_data = requests.get(
        f"https://opendev.org/openstack/{project}/raw/branch/master/{chart}/values.yaml"
    ).text
    data = yaml.safe_load(raw_data)

    chart_keys = data["endpoints"].keys() - ignored_keys
    atmosphere_keys = osh_endpoints.Endpoints.for_chart(chart).to_native().keys()

    assert chart_keys == atmosphere_keys


def test_endpoint_for_chart_memcached():
    endpoints = osh_endpoints.Endpoints.for_chart("memcached")

    assert {
        "oslo_cache": {
            "auth": {
                "memcache_secret_key": CONF.memcached.secret_key,
            }
        }
    } == endpoints.to_primitive()
