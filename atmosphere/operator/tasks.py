import glob
import json
import logging
import os
import subprocess

import kopf
import mergedeep
import pkg_resources
import pykube
import yaml
from oslo_utils import strutils
from taskflow import task
from tenacity import retry, retry_if_result, stop_after_delay, wait_fixed

from atmosphere import clients
from atmosphere.operator import constants, utils

LOG = logging.getLogger(__name__)


class BuildApiClient(task.Task):
    default_provides = "api"

    def execute(self) -> pykube.HTTPClient:
        return clients.get_pykube_api()


class ApplyKubernetesObjectTask(task.Task):
    def __init__(self, rebind={}, **kwargs):
        rebind["api"] = "api"
        super().__init__(
            rebind=rebind,
            **kwargs,
        )

    def generate_object(self, *args, **kwargs) -> pykube.objects.APIObject:
        raise NotImplementedError

    def _log(self, resource: pykube.objects.APIObject, message: str):
        resource_info = {
            "kind": resource.kind,
        }

        resource_info["name"] = resource.name
        if resource.namespace:
            resource_info["namespace"] = resource.namespace

        # Generate user friendly string from resource info
        resource_info_str = ", ".join([f"{k}={v}" for k, v in resource_info.items()])
        LOG.info(f"[{resource_info_str}] {message}")

    def wait_for_resource(
        self, resource: pykube.objects.APIObject
    ) -> pykube.objects.APIObject:
        self._log(resource, f"{resource.kind} is ready")
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

        self._log(
            resource,
            "Server-side apply completed, starting to wait for resource to be ready...",
        )

        return self.wait_for_resource(resource)

    def execute(self, *args, **kwargs):

        resource = self.generate_object(*args, **kwargs)
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

        self._log(
            resource,
            "Server-side apply completed, starting to wait for resource to be ready...",
        )
        self.wait_for_resource(resource)

        return {
            self.name: resource,
        }


class ApplyNamespaceTask(ApplyKubernetesObjectTask):
    def __init__(self, name: str, provides: str = "namespace"):
        super().__init__(
            name=f"ApplyNamespaceTask(name={name})",
            inject={"name": name},
            provides=provides,
        )

    def generate_object(
        self, api: pykube.HTTPClient, name: str, *args, **kwargs
    ) -> pykube.Namespace:
        return pykube.Namespace(
            api,
            {
                "apiVersion": pykube.Namespace.version,
                "kind": pykube.Namespace.kind,
                "metadata": {
                    "name": name,
                },
            },
        )


class ApplySecretTask(ApplyKubernetesObjectTask):
    def __init__(self, name: str, inject: dict, **kwargs):
        super().__init__(
            name=f"ApplySecretTask(name={name})",
            inject={"name": name, **inject},
            **kwargs,
        )

    def generate_object(
        self,
        api: pykube.HTTPClient,
        namespace: pykube.Namespace,
        name: str,
        data: dict,
        *args,
        **kwargs,
    ) -> pykube.Secret:
        return pykube.Secret(
            api,
            {
                "apiVersion": pykube.Secret.version,
                "kind": pykube.Secret.kind,
                "metadata": {
                    "name": name,
                    "namespace": namespace.name,
                },
                "stringData": data,
            },
        )


class ApplyServiceTask(ApplyKubernetesObjectTask):
    def __init__(self, name: str, inject: dict, **kwargs):
        super().__init__(
            name=f"ApplyServiceTask(name={name})",
            inject={"name": name, **inject},
            **kwargs,
        )

    def generate_object(
        self,
        api: pykube.HTTPClient,
        namespace: pykube.Namespace,
        name: str,
        labels: dict,
        ports: list,
        *args,
        **kwargs,
    ) -> pykube.Service:
        return pykube.Service(
            api,
            {
                "apiVersion": pykube.Service.version,
                "kind": pykube.Service.kind,
                "metadata": {
                    "name": name,
                    "namespace": namespace.name,
                    "labels": labels,
                },
                "spec": {
                    "selector": labels,
                    "ports": ports,
                },
            },
        )


class HelmRepository(pykube.objects.NamespacedAPIObject):
    version = "source.toolkit.fluxcd.io/v1beta2"
    endpoint = "helmrepositories"
    kind = "HelmRepository"


class ApplyHelmRepositoryTask(ApplyKubernetesObjectTask):
    def generate_object(
        self,
        api: pykube.HTTPClient,
        namespace: pykube.Namespace,
        repository_name: str,
        url: str,
        *args,
        **kwargs,
    ) -> HelmRepository:
        return HelmRepository(
            api,
            {
                "apiVersion": HelmRepository.version,
                "kind": HelmRepository.kind,
                "metadata": {
                    "name": repository_name,
                    "namespace": namespace.name,
                },
                "spec": {
                    "interval": "1m",
                    "url": url,
                },
            },
        )


class HelmRelease(pykube.objects.NamespacedAPIObject):
    version = "helm.toolkit.fluxcd.io/v2beta1"
    endpoint = "helmreleases"
    kind = "HelmRelease"


class ApplyHelmReleaseTask(ApplyKubernetesObjectTask):
    def __init__(self, config: dict, rebind: dict = {}):
        super().__init__(
            name=f"ApplyHelmReleaseTask(release_name={config['release_name']})",
            inject=config,
            rebind=rebind,
            provides=f"{config['release_name'].replace('-', '_')}_helm_release",
        )

    def generate_object(
        self,
        api: pykube.HTTPClient,
        namespace: pykube.objects.Namespace,
        release_name: str,
        helm_repository: HelmRepository,
        chart_name: str,
        chart_version: str,
        values: dict,
        values_from: list,
        spec: dict,
        alias: str = "",
        *args,
        **kwargs,
    ) -> HelmRelease:
        config_key = chart_name if not alias else alias
        if config_key in spec:
            values = mergedeep.merge(
                spec[config_key].get("overrides", {}),
                values,
            )
        return HelmRelease(
            api,
            {
                "apiVersion": HelmRelease.version,
                "kind": HelmRelease.kind,
                "metadata": {
                    "name": release_name,
                    "namespace": namespace.name,
                },
                "spec": {
                    "interval": "60s",
                    "chart": {
                        "spec": {
                            "chart": chart_name,
                            "version": chart_version,
                            "sourceRef": {
                                "kind": helm_repository.kind,
                                "name": helm_repository.name,
                                "namespace": helm_repository.namespace,
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

    @retry(
        retry=retry_if_result(lambda f: f is False),
        stop=stop_after_delay(300),
        wait=wait_fixed(1),
    )
    def wait_for_resource(self, resource: HelmRelease) -> HelmRelease:
        resource.reload()

        # TODO(mnaser): detect potential changes and wait

        # Generate map with list of conditions
        conditions = {
            condition["type"]: {
                "status": strutils.bool_from_string(condition["status"]),
                "reason": condition.get("reason"),
                "message": condition.get("message"),
            }
            for condition in resource.obj["status"].get("conditions", [])
        }

        # Generate user-friendly string with conditions and their status
        conditions_str = ", ".join(
            f"{condition}={info['status']} ({info['reason']})"
            for condition, info in conditions.items()
        )

        # Log current conditions
        self._log(
            resource,
            f"Waiting for HelmRelease to be ready, current conditions: {conditions_str}",
        )

        # Unless we're not ready and released, we're not ready
        if conditions.get("Ready", {}).get("status") and conditions.get(
            "Released", {}
        ).get("status"):
            self._log(resource, "HelmRelease is ready")
            return resource

        # If the installation has failed, let's raise an exception
        if conditions.get("Ready", {}).get("reason") == "InstallFailed":
            raise kopf.TemporaryError(
                f"HelmRelease installation failed: {conditions.get('Ready', {}).get('message')}"
            )

        return False


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


class RabbitmqCluster(pykube.objects.NamespacedAPIObject):
    version = "rabbitmq.com/v1beta1"
    endpoint = "rabbitmqclusters"
    kind = "RabbitmqCluster"


class ApplyRabbitmqClusterTask(ApplyKubernetesObjectTask):
    def __init__(self, cluster_name: str):
        super().__init__(
            name=f"ApplyRabbitmqClusterTask(cluster_name={cluster_name})",
            inject={"cluster_name": cluster_name},
            rebind={
                "rabbitmq_cluster_operator_helm_release": "rabbitmq_cluster_operator_helm_release",
                "namespace": "openstack_namespace",
            },
            provides=f"{cluster_name}_rabbitmq_cluster",
        )

    def generate_object(
        self,
        api: pykube.HTTPClient,
        namespace: pykube.Namespace,
        rabbitmq_cluster_operator_helm_release: HelmRelease,
        cluster_name: str,
        *args,
        **kwargs,
    ) -> dict:
        # NOTE(mnaser): This is a workaround to make sure the CRD is installed
        assert rabbitmq_cluster_operator_helm_release.exists()

        return RabbitmqCluster(
            api,
            {
                "apiVersion": RabbitmqCluster.version,
                "kind": RabbitmqCluster.kind,
                "metadata": {
                    "name": f"rabbitmq-{cluster_name}",
                    "namespace": namespace.name,
                },
                "spec": {
                    "affinity": {
                        "nodeAffinity": {
                            "requiredDuringSchedulingIgnoredDuringExecution": {
                                "nodeSelectorTerms": [
                                    {
                                        "matchExpressions": [
                                            {
                                                "key": "openstack-control-plane",
                                                "operator": "In",
                                                "values": ["enabled"],
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    },
                    "rabbitmq": {
                        "additionalConfig": "vm_memory_high_watermark.relative = 0.9\n"
                    },
                    "resources": {
                        "requests": {"cpu": "500m", "memory": "1Gi"},
                        "limits": {"cpu": "1", "memory": "2Gi"},
                    },
                    "terminationGracePeriodSeconds": 15,
                },
            },
        )


class PerconaXtraDBCluster(pykube.objects.NamespacedAPIObject):
    version = "pxc.percona.com/v1-10-0"
    endpoint = "perconaxtradbclusters"
    kind = "PerconaXtraDBCluster"


class ApplyPerconaXtraDBClusterTask(ApplyKubernetesObjectTask):
    def generate_object(
        self,
        api: pykube.HTTPClient,
        namespace: pykube.Namespace,
        spec: dict,
        pxc_operator_helm_release: HelmRelease,
        *args,
        **kwargs,
    ) -> PerconaXtraDBCluster:
        # NOTE(mnaser): This is a workaround to make sure the CRD is installed
        assert pxc_operator_helm_release.exists()

        return PerconaXtraDBCluster(
            api,
            {
                "apiVersion": PerconaXtraDBCluster.version,
                "kind": PerconaXtraDBCluster.kind,
                "metadata": {
                    "name": "percona-xtradb",
                    "namespace": namespace.name,
                },
                "spec": {
                    "crVersion": "1.10.0",
                    "secretsName": "percona-xtradb",
                    "pxc": {
                        "size": 3,
                        "image": utils.get_image_ref(
                            spec["imageRepository"], "percona_xtradb_cluster"
                        ),
                        "autoRecovery": True,
                        "configuration": "[mysqld]\nmax_connections=8192\n",
                        "sidecars": [
                            {
                                "name": "exporter",
                                "image": utils.get_image_ref(
                                    spec["imageRepository"], "mysqld_exporter"
                                ),
                                "ports": [{"name": "metrics", "containerPort": 9104}],
                                "livenessProbe": {
                                    "httpGet": {"path": "/", "port": 9104}
                                },
                                "env": [
                                    {
                                        "name": "MONITOR_PASSWORD",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "name": "percona-xtradb",
                                                "key": "monitor",
                                            }
                                        },
                                    },
                                    {
                                        "name": "DATA_SOURCE_NAME",
                                        "value": "monitor:$(MONITOR_PASSWORD)@(localhost:3306)/",
                                    },
                                ],
                            }
                        ],
                        "nodeSelector": constants.NODE_SELECTOR_CONTROL_PLANE,
                        "volumeSpec": {
                            "persistentVolumeClaim": {
                                "resources": {"requests": {"storage": "160Gi"}}
                            }
                        },
                    },
                    "haproxy": {
                        "enabled": True,
                        "size": 3,
                        "image": utils.get_image_ref(
                            spec["imageRepository"], "percona_xtradb_cluster_haproxy"
                        ),
                        "nodeSelector": constants.NODE_SELECTOR_CONTROL_PLANE,
                    },
                },
            },
        )

    @retry(
        retry=retry_if_result(lambda f: f is False),
        stop=stop_after_delay(300),
        wait=wait_fixed(1),
    )
    def wait_for_resource(self, resource: HelmRelease) -> HelmRelease:
        resource.reload()

        self._log(
            resource,
            f"Waiting for PerconaXtraDBCluster to be ready, current status: {resource.obj['status']['state']}",
        )

        if resource.obj["status"]["state"] == "ready":
            self._log(resource, "PerconaXtraDBCluster is ready")
            return resource

        return False


class GenerateSecrets(ApplyKubernetesObjectTask):
    def generate_object(
        self, api: pykube.HTTPClient, namespace: str, name: str, *args, **kwargs
    ) -> pykube.Secret:
        # TODO(mnaser): We should generate this if it's missing, but for now
        #               assume that it exists.
        secret_name = f"{name}-secrets"
        return pykube.Secret.objects(api, namespace=namespace).get(name=secret_name)


class GenerateImageTagsConfigMap(ApplyKubernetesObjectTask):
    def generate_object(
        self,
        api: pykube.HTTPClient,
        namespace: str,
        name: str,
        spec: dict,
        *args,
        **kwargs,
    ) -> pykube.ConfigMap:
        return pykube.ConfigMap(
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
    def _generate_base(self, rabbitmq: RabbitmqCluster, spec: dict) -> dict:
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
                        "default": rabbitmq.name,
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

    def execute(self, chart_name: str, rabbitmq: RabbitmqCluster, spec: dict) -> dict:
        return mergedeep.merge(
            {},
            self._generate_base(rabbitmq, spec),
            getattr(self, f"_generate_{chart_name}")(spec),
            spec[chart_name].get("overrides", {}),
        )


class GenerateMagnumChartValuesFrom(task.Task):
    def execute(
        self,
        image_tags: pykube.ConfigMap,
        secrets: pykube.Secret,
        rabbitmq: RabbitmqCluster,
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
                "name": f"{rabbitmq.name}-default-user",
                "targetPath": "endpoints.oslo_messaging.auth.admin.username",
                "valuesKey": "username",
            },
            {
                "kind": pykube.Secret.kind,
                "name": f"{rabbitmq.name}-default-user",
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


class ApplyIngressTask(ApplyKubernetesObjectTask):
    def generate_object(
        self,
        api: pykube.HTTPClient,
        namespace: str,
        endpoint: str,
        spec: dict,
        chart_values: dict,
        release_values: dict,
        *args,
        **kwargs,
    ) -> pykube.Ingress:
        host = release_values["endpoints"][endpoint]["host_fqdn_override"]["public"][
            "host"
        ]
        service_name = chart_values["endpoints"][endpoint]["hosts"]["default"]
        service_port = chart_values["endpoints"][endpoint]["port"]["api"]["default"]

        return pykube.Ingress(
            api,
            {
                "apiVersion": pykube.Ingress.version,
                "kind": pykube.Ingress.kind,
                "metadata": {
                    "name": endpoint.replace("_", "-"),
                    "namespace": namespace,
                    "annotations": {
                        "cert-manager.io/cluster-issuer": spec[
                            "certManagerClusterIssuer"
                        ],
                    },
                },
                "spec": {
                    "ingressClassName": spec["ingressClassName"],
                    "rules": [
                        {
                            "host": host,
                            "http": {
                                "paths": [
                                    {
                                        "path": "/",
                                        "pathType": "Prefix",
                                        "backend": {
                                            "service": {
                                                "name": service_name,
                                                "port": {
                                                    "number": service_port,
                                                },
                                            },
                                        },
                                    },
                                ],
                            },
                        },
                    ],
                    "tls": [{"secretName": f"{service_name}-certs", "hosts": [host]}],
                },
            },
        )


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
