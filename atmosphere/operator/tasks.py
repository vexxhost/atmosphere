import glob
import json
import logging
import os
import subprocess

import mergedeep
import pkg_resources
import pykube
import yaml
from oslo_utils import strutils
from taskflow import task
from tenacity import retry, retry_if_result, stop_after_delay, wait_fixed

from atmosphere.operator import constants, utils

LOG = logging.getLogger(__name__)


class ApplyKubernetesObjectTask(task.Task):
    def generate_object(self, *args, **kwargs) -> pykube.objects.APIObject:
        raise NotImplementedError

    def wait_for_resource(self, resource: pykube.objects.APIObject):
        return resource

    def _apply(self, resource: pykube.objects.APIObject) -> pykube.objects.APIObject:
        resp = resource.api.patch(
            **resource.api_kwargs(
                headers={
                    "Content-Type": "application/apply-patch+yaml",
                },
                params={
                    "fieldManager": "atmosphere-operator",
                    "force": True,
                },
                data=json.dumps(resource.obj),
            )
        )

        resource.api.raise_for_status(resp)
        resource.set_obj(resp.json())

        return self.wait_for_resource(resource)


class InstallClusterApiTask(task.Task):
    def execute(self, spec: dict):
        cluster_api_images = [
            i for i in constants.IMAGE_LIST if i.startswith("cluster_api")
        ]

        # TODO(mnaser): Move CAPI and CAPO to run on control plane
        manifests_path = pkg_resources.resource_filename(__name__, "manifests")
        manifest_files = glob.glob(os.path.join(manifests_path, "capi-*.yml"))

        for manifest in manifest_files:
            with open(manifest) as fd:
                data = fd.read()

            # NOTE(mnaser): Replace all the images for Cluster API
            for image in cluster_api_images:
                data = data.replace(
                    utils.get_image_ref(image).string(),
                    utils.get_image_ref(
                        image, override_registry=spec["imageRepository"]
                    ).string(),
                )

            subprocess.run(
                "kubectl apply -f -",
                shell=True,
                check=True,
                input=data,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


class HelmRelease(pykube.objects.NamespacedAPIObject):
    version = "helm.toolkit.fluxcd.io/v2beta1"
    endpoint = "helmreleases"
    kind = "HelmRelease"


class ApplyHelmReleaseTask(ApplyKubernetesObjectTask):
    def execute(
        self,
        api: pykube.HTTPClient,
        namespace: str,
        release_name: str,
        helm_repository: str,
        chart_name: str,
        chart_version: str,
        values: dict,
        values_from: list,
    ) -> HelmRelease:
        resource = HelmRelease(
            api,
            {
                "apiVersion": HelmRelease.version,
                "kind": HelmRelease.kind,
                "metadata": {
                    "name": release_name,
                    "namespace": namespace,
                },
                "spec": {
                    "interval": "60s",
                    "chart": {
                        "spec": {
                            "chart": chart_name,
                            "version": chart_version,
                            "sourceRef": {
                                "kind": "HelmRepository",
                                "name": helm_repository,
                            },
                        }
                    },
                    "install": {
                        "crds": "CreateReplace",
                        "disableWait": True,
                    },
                    "upgrade": {
                        "crds": "CreateReplace",
                        "disableWait": True,
                    },
                    "values": values,
                    "valuesFrom": values_from,
                },
            },
        )

        return self._apply(resource)

    @retry(
        retry=retry_if_result(lambda f: f is False),
        stop=stop_after_delay(300),
        wait=wait_fixed(1),
    )
    def wait_for_resource(self, resource: HelmRelease, *args, **kwargs) -> bool:
        # TODO(mnaser): detect potential changes and wait
        resource.reload()

        conditions = {
            condition["type"]: strutils.bool_from_string(condition["status"])
            for condition in resource.obj["status"].get("conditions", [])
        }

        if not conditions.get("Ready", False) and conditions.get("Released", False):
            return False
        return resource


class GenerateSecrets(ApplyKubernetesObjectTask):
    def execute(
        self, api: pykube.HTTPClient, namespace: str, name: str
    ) -> pykube.Secret:
        # TODO(mnaser): We should generate this if it's missing, but for now
        #               assume that it exists.
        secret_name = f"{name}-secrets"
        return pykube.Secret.objects(api, namespace=namespace).get(name=secret_name)


class GenerateImageTagsConfigMap(ApplyKubernetesObjectTask):
    def execute(
        self, api: pykube.HTTPClient, namespace: str, name: str, spec: dict
    ) -> pykube.ConfigMap:
        resource = pykube.ConfigMap(
            api,
            {
                "apiVersion": pykube.ConfigMap.version,
                "kind": pykube.ConfigMap.kind,
                "metadata": {
                    "name": f"{name}-images",
                    "namespace": namespace,
                },
                "data": {
                    "values.yaml": yaml.dump(
                        {
                            "images": {
                                "tags": {
                                    image_name: utils.get_image_ref(
                                        image_name,
                                        override_registry=spec["imageRepository"],
                                    ).string()
                                    for image_name in constants.IMAGE_LIST.keys()
                                }
                            }
                        }
                    )
                },
            },
        )

        return self._apply(resource)


class GetChartValues(task.Task):
    def execute(
        self,
        helm_repository: str,
        helm_repository_url: str,
        chart_name: str,
        chart_version: str,
    ) -> dict:
        # TODO(mnaser): Once we move towards air-gapped deployments, we should
        #               refactor this to pull from local OCI registry instead.
        subprocess.check_call(
            f"helm repo add --force-update {helm_repository} {helm_repository_url}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.check_call(
            "helm repo update",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        data = subprocess.check_output(
            f"helm show values {helm_repository}/{chart_name} --version {chart_version}",
            shell=True,
        )
        return yaml.safe_load(data)


class GenerateReleaseValues(task.Task):
    def _generate_base(self, rabbitmq: str, spec: dict) -> dict:
        return {
            "endpoints": {
                "identity": {
                    "auth": {
                        "admin": {
                            "username": f"admin-{spec['regionName']}",
                            "region_name": spec["regionName"],
                        },
                    },
                },
                "oslo_db": {
                    "hosts": {
                        # TODO(mnaser): Move this into a dependency
                        "default": "percona-xtradb-haproxy",
                    },
                },
                "oslo_messaging": {
                    "statefulset": None,
                    "hosts": {
                        # TODO(mnaser): handle scenario when those don't exist
                        "default": rabbitmq,
                    },
                },
            },
        }

    def _generate_magnum(self, spec: dict) -> dict:
        return {
            "endpoints": {
                "container_infra": {
                    "host_fqdn_override": {
                        "public": {"host": spec["magnum"]["endpoint"]}
                    },
                    "port": {"api": {"public": 443}},
                    "scheme": {"public": "https"},
                },
                "identity": {
                    "auth": {
                        "magnum": {
                            "username": f"magnum-{spec['regionName']}",
                            "region_name": spec["regionName"],
                        },
                        "magnum_stack_user": {
                            "username": f"magnum-domain-{spec['regionName']}",
                            "region_name": spec["regionName"],
                        },
                    },
                },
            },
            "conf": {
                "magnum": {
                    "DEFAULT": {"log_config_append": None},
                    "barbican_client": {
                        "endpoint_type": "internalURL",
                        "region_name": spec["regionName"],
                    },
                    "cinder_client": {
                        "endpoint_type": "internalURL",
                        "region_name": spec["regionName"],
                    },
                    "cluster_template": {
                        "kubernetes_allowed_network_drivers": "calico",
                        "kubernetes_default_network_driver": "calico",
                    },
                    "conductor": {"workers": 4},
                    "drivers": {
                        "verify_ca": False,
                    },
                    "glance_client": {
                        "endpoint_type": "internalURL",
                        "region_name": spec["regionName"],
                    },
                    "heat_client": {
                        "endpoint_type": "internalURL",
                        "region_name": spec["regionName"],
                    },
                    "keystone_auth": {
                        "auth_url": "http://keystone-api.openstack.svc.cluster.local:5000/v3",
                        "user_domain_name": "service",
                        "username": f"magnum-{spec['regionName']}",
                        # NOTE(mnaser): Magnum does not allow changing the interface to internal
                        #               so we workaround with this for now.
                        "insecure": True,
                    },
                    "keystone_authtoken": {
                        # NOTE(mnaser): Magnum does not allow changing the interface to internal
                        #               so we workaround with this for now.
                        "insecure": True,
                    },
                    "magnum_client": {"region_name": spec["regionName"]},
                    "neutron_client": {
                        "endpoint_type": "internalURL",
                        "region_name": spec["regionName"],
                    },
                    "nova_client": {
                        "endpoint_type": "internalURL",
                        "region_name": spec["regionName"],
                    },
                    "octavia_client": {
                        "endpoint_type": "internalURL",
                        "region_name": spec["regionName"],
                    },
                }
            },
            "pod": {
                "replicas": {
                    "api": 3,
                    "conductor": 3,
                },
            },
            "manifests": {
                "ingress_api": False,
                "service_ingress_api": False,
            },
        }

    def execute(self, chart_name: str, spec: dict) -> dict:
        return mergedeep.merge(
            {},
            self._generate_base(f"rabbitmq-{chart_name}", spec),
            getattr(self, f"_generate_{chart_name}")(spec),
            spec[chart_name].get("overrides", {}),
        )


class GenerateMagnumChartValuesFrom(task.Task):
    def execute(
        self,
        chart_name: str,
        image_tags: pykube.ConfigMap,
        secrets: pykube.Secret,
    ) -> dict:
        return [
            {
                "kind": pykube.ConfigMap.kind,
                "name": image_tags.name,
            },
            {
                "kind": pykube.Secret.kind,
                "name": secrets.name,
                "targetPath": "conf.magnum.keystone_auth.password",
                "valuesKey": "magnum-keystone-password",
            },
            {
                "kind": pykube.Secret.kind,
                "name": secrets.name,
                "targetPath": "endpoints.oslo_cache.auth.memcache_secret_key",
                "valuesKey": "memcache-secret-key",
            },
            {
                "kind": pykube.Secret.kind,
                "name": secrets.name,
                "targetPath": "endpoints.identity.auth.admin.password",
                "valuesKey": "keystone-admin-password",
            },
            {
                "kind": pykube.Secret.kind,
                "name": secrets.name,
                "targetPath": "endpoints.identity.auth.magnum.password",
                "valuesKey": "magnum-keystone-password",
            },
            {
                "kind": pykube.Secret.kind,
                "name": secrets.name,
                "targetPath": "endpoints.identity.auth.magnum_stack_user.password",
                "valuesKey": "magnum-keystone-password",
            },
            {
                "kind": pykube.Secret.kind,
                "name": "percona-xtradb",
                "targetPath": "endpoints.oslo_db.auth.admin.password",
                "valuesKey": "root",
            },
            {
                "kind": pykube.Secret.kind,
                "name": secrets.name,
                "targetPath": "endpoints.oslo_db.auth.magnum.password",
                "valuesKey": "magnum-database-password",
            },
            {
                "kind": pykube.Secret.kind,
                "name": f"rabbitmq-{chart_name}-default-user",
                "targetPath": "endpoints.oslo_messaging.auth.admin.username",
                "valuesKey": "username",
            },
            {
                "kind": pykube.Secret.kind,
                "name": f"rabbitmq-{chart_name}-default-user",
                "targetPath": "endpoints.oslo_messaging.auth.admin.password",
                "valuesKey": "password",
            },
            {
                "kind": pykube.Secret.kind,
                "name": secrets.name,
                "targetPath": "endpoints.oslo_messaging.auth.magnum.password",
                "valuesKey": "magnum-rabbitmq-password",
            },
        ]


class GenerateOpenStackHelmEndpoints(task.Task):
    SKIPPED_ENDPOINTS = (
        "cluster_domain_suffix",
        "local_image_registry",
        "oci_image_registry",
        "fluentd",
    )

    def __init__(
        self,
        repository_name: str,
        repository_url: str,
        chart_name: str,
        chart_version: str,
        *args,
        **kwargs,
    ):
        self._repository_name = repository_name
        self._repository_url = repository_url
        self._chart_name = chart_name
        self._chart_version = chart_version

        super().__init__(*args, **kwargs)

    def _get_values(self):
        # TODO(mnaser): Once we move towards air-gapped deployments, we should
        #               refactor this to pull from local OCI registry instead.
        subprocess.check_call(
            f"helm repo add --force-update {self._repository_name} {self._repository_url}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.check_call(
            "helm repo update",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        data = subprocess.check_output(
            f"helm show values {self._repository_name}/{self._chart_name} --version {self._chart_version}",
            shell=True,
        )
        return yaml.safe_load(data)

    def _generate_oslo_messaging(self):
        return {
            "statefulset": None,
            "hosts": {
                "default": f"rabbitmq-{self._chart_name}",
            },
        }

    def _generate_orchestration(self):
        return {}

    def _generate_key_manager(self):
        return {}

    def _generate_oslo_db(self):
        return {"hosts": {"default": "percona-xtradb-haproxy"}}

    def _generate_identity(self):
        return {}

    def _generate_oslo_cache(self):
        # TODO: only generate if we're getting endpoints for memcached chart
        return {}

    def _generate_container_infra(self):
        return {}

    def execute(self, *args, **kwargs):
        endpoints = (
            self._get_values().get("endpoints", {}).keys() - self.SKIPPED_ENDPOINTS
        )
        return {"endpoints": {k: getattr(self, "_generate_" + k)() for k in endpoints}}
