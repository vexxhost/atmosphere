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
    @property
    def api(self):
        return clients.get_pykube_api()

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


class ApplyNamespaceTask(ApplyKubernetesObjectTask):
    def __init__(self, name: str, provides: str = "namespace"):
        super().__init__(
            name=f"ApplyNamespaceTask(name={name})",
            inject={"name": name},
            provides=provides,
        )

    def execute(self, api: pykube.HTTPClient, name: str) -> pykube.Namespace:
        resource = pykube.Namespace(
            api,
            {
                "apiVersion": pykube.Namespace.version,
                "kind": pykube.Namespace.kind,
                "metadata": {
                    "name": name,
                },
            },
        )

        return self._apply(resource)


class ApplyServiceTask(ApplyKubernetesObjectTask):
    def __init__(self, name: str, inject: dict):
        super().__init__(
            name=f"ApplyServiceTask(name={name})",
            inject={"name": name, **inject},
        )

    def execute(
        self,
        api: pykube.HTTPClient,
        namespace: pykube.Namespace,
        name: str,
        labels: dict,
        ports: list,
    ) -> pykube.Service:
        resource = pykube.Service(
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

        return self._apply(resource)


class HelmRepository(pykube.objects.NamespacedAPIObject):
    version = "source.toolkit.fluxcd.io/v1beta2"
    endpoint = "helmrepositories"
    kind = "HelmRepository"


class ApplyHelmRepositoryTask(ApplyKubernetesObjectTask):
    def execute(
        self,
        api: pykube.HTTPClient,
        namespace: pykube.Namespace,
        repository_name: str,
        url: str,
    ) -> HelmRepository:
        resource = HelmRepository(
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

        return self._apply(resource)


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

    def execute(
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
    ) -> HelmRelease:
        config_key = chart_name if not alias else alias
        if config_key in spec:
            values = mergedeep.merge(
                spec[config_key].get("overrides", {}),
                values,
            )
        resource = HelmRelease(
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

        return self._apply(resource)

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


class ClusterIssuer(pykube.objects.APIObject):
    version = "cert-manager.io/v1"
    endpoint = "clusterissuers"
    kind = "ClusterIssuer"


class Certificate(pykube.objects.NamespacedAPIObject):
    version = "cert-manager.io/v1"
    endpoint = "certificates"
    kind = "Certificate"


class GetClusterIssuerTask(ApplyKubernetesObjectTask):
    def execute(self, api: pykube.HTTPClient, spec: dict) -> ClusterIssuer:
        issuer_spec = spec["certManager"]["issuer"]
        if issuer_spec["existing"]:
            return ClusterIssuer.objects(api).get(name=issuer_spec["existing"])


class ApplyClusterIssuerTask(ApplyKubernetesObjectTask):
    def execute(
        self, api: pykube.HTTPClient, cert_manager_helm_release: HelmRelease, spec: dict
    ) -> ClusterIssuer:
        issuer_spec = spec["certManager"]["issuer"]["config"]
        objects = [
            ClusterIssuer(
                api,
                {
                    "apiVersion": ClusterIssuer.version,
                    "kind": ClusterIssuer.kind,
                    "metadata": {
                        "name": "self-signed",
                    },
                    "spec": {
                        "selfSigned": {},
                    },
                },
            )
        ]

        if issuer_spec["type"] == "acme":
            spec = {
                "acme": {
                    "email": issuer_spec["email"],
                    "server": issuer_spec["server"],
                    "privateKeySecretRef": {
                        "name": "cert-manager-issuer-account-key",
                    },
                },
            }

            if issuer_spec["solver"]["type"] == "http":
                spec["acme"]["solvers"] = [
                    {
                        "http01": {
                            "ingress": {
                                "class": "openstack",
                            },
                        },
                    },
                ]
            elif issuer_spec["solver"]["type"] == "rfc2136":
                # NOTE(mnaser): We have to create a secret containing the AWS
                #               credentials in this case.
                objects.append(
                    pykube.objects.Secret(
                        api,
                        {
                            "apiVersion": "v1",
                            "kind": "Secret",
                            "metadata": {
                                "name": "cert-manager-issuer-tsig-secret-key",
                                "namespace": cert_manager_helm_release.namespace,
                            },
                            "stringData": {
                                "tsig-secret-key": issuer_spec["solver"]["tsig_secret"],
                            },
                        },
                    )
                )

                spec["acme"]["solvers"] = [
                    {
                        "dns01": {
                            "rfc2136": {
                                "nameserver": issuer_spec["solver"]["nameserver"],
                                "tsigAlgorithm": issuer_spec["solver"][
                                    "tsig_algorithm"
                                ],
                                "tsigKeyName": issuer_spec["solver"]["tsig_key_name"],
                                "tsigSecretSecretRef": {
                                    "name": "cert-manager-issuer-tsig-secret-key",
                                    "key": "tsig-secret-key",
                                },
                            },
                        },
                    },
                ]
            elif issuer_spec["solver"]["type"] == "route53":
                # NOTE(mnaser): We have to create a secret containing the AWS
                #               credentials in this case.
                objects.append(
                    pykube.objects.Secret(
                        api,
                        {
                            "apiVersion": "v1",
                            "kind": "Secret",
                            "metadata": {
                                "name": "cert-manager-issuer-route53-credentials",
                                "namespace": cert_manager_helm_release.namespace,
                            },
                            "stringData": {
                                "secret-access-key": issuer_spec["solver"][
                                    "secret_access_key"
                                ]
                            },
                        },
                    ),
                )

                spec["acme"]["solvers"] = [
                    {
                        "dns01": {
                            "route53": {
                                "region": issuer_spec["solver"]["region"],
                                "hostedZoneID": issuer_spec["solver"]["hosted_zone_id"],
                                "accessKeyID": issuer_spec["solver"]["access_key_id"],
                                "secretAccessKeySecretRef": {
                                    "name": "cert-manager-issuer-route53-credentials",
                                    "key": "secret-access-key",
                                },
                            },
                        },
                    },
                ]
        elif issuer_spec["type"] == "ca":
            # NOTE(mnaser): We have to create a secret containing the CA
            #               certificate and key in this case.
            objects.append(
                pykube.objects.Secret(
                    api,
                    {
                        "apiVersion": "v1",
                        "kind": "Secret",
                        "metadata": {
                            "name": "cert-manager-issuer-ca",
                            "namespace": cert_manager_helm_release.namespace,
                        },
                        "stringData": {
                            "tls.crt": issuer_spec["certificate"],
                            "tls.key": issuer_spec["private_key"],
                        },
                    },
                ),
            )

            spec = {
                "ca": {
                    "secretName": "cert-manager-issuer-ca",
                }
            }
        elif issuer_spec["type"] == "self-signed":
            # NOTE(mnaser): We have to setup the self-signed CA in this case
            objects += [
                Certificate(
                    api,
                    {
                        "apiVersion": Certificate.version,
                        "kind": Certificate.kind,
                        "metadata": {
                            "name": "self-signed-ca",
                            "namespace": cert_manager_helm_release.namespace,
                        },
                        "spec": {
                            "isCA": True,
                            "commonName": "selfsigned-ca",
                            "secretName": "cert-manager-selfsigned-ca",
                            "duration": "86400h",
                            "renewBefore": "360h",
                            "privateKey": {"algorithm": "ECDSA", "size": 256},
                            "issuerRef": {
                                "kind": "ClusterIssuer",
                                "name": "self-signed",
                            },
                        },
                    },
                )
            ]

            spec = {
                "ca": {
                    "secretName": "cert-manager-selfsigned-ca",
                }
            }

        cluster_issuer = ClusterIssuer(
            api,
            {
                "apiVersion": ClusterIssuer.version,
                "kind": ClusterIssuer.kind,
                "metadata": {
                    "name": "atmosphere",
                },
                "spec": spec,
            },
        )

        for obj in objects:
            self._apply(obj)
        return self._apply(cluster_issuer)


class InstallClusterApiTask(task.Task):
    def execute(self, cluster_issuer: ClusterIssuer):
        # NOTE(mnaser): This is a hack to make sure the cert-manager CRDs are
        #               installed before we try install the Cluster API.
        assert cluster_issuer.exists()

        # TODO(mnaser): Move CAPI and CAPO to run on control plane
        manifests_path = pkg_resources.resource_filename(__name__, "manifests")
        manifest_files = glob.glob(os.path.join(manifests_path, "capi-*.yml"))

        for manifest in manifest_files:
            with open(manifest) as fd:
                subprocess.check_call(
                    "kubectl apply -f -",
                    shell=True,
                    stdin=fd,
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
            provides=f"{cluster_name}_rabbitmq_cluster",
        )

    def execute(
        self,
        api: pykube.HTTPClient,
        namespace: pykube.Namespace,
        rabbitmq_cluster_operator_helm_release: HelmRelease,
        cluster_name: str,
    ) -> dict:
        # NOTE(mnaser): This is a workaround to make sure the CRD is installed
        assert rabbitmq_cluster_operator_helm_release.exists()

        resource = RabbitmqCluster(
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

        return self._apply(resource)


class PerconaXtraDBCluster(pykube.objects.NamespacedAPIObject):
    version = "pxc.percona.com/v1-10-0"
    endpoint = "perconaxtradbclusters"
    kind = "PerconaXtraDBCluster"


class ApplyPerconaXtraDBClusterTask(ApplyKubernetesObjectTask):
    def execute(
        self,
        namespace: pykube.Namespace,
        spec: dict,
        pxc_operator_helm_release: HelmRelease,
    ) -> PerconaXtraDBCluster:
        # NOTE(mnaser): This is a workaround to make sure the CRD is installed
        assert pxc_operator_helm_release.exists()

        resource = PerconaXtraDBCluster(
            self.api,
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

        return self._apply(resource)

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
    def execute(
        self, api: pykube.HTTPClient, namespace: pykube.Namespace, name: str
    ) -> pykube.Secret:
        # TODO(mnaser): We should generate this if it's missing, but for now
        #               assume that it exists.
        secret_name = f"{name}-secrets"
        return pykube.Secret.objects(api, namespace=namespace.name).get(
            name=secret_name
        )


class GenerateImageTagsConfigMap(ApplyKubernetesObjectTask):
    def execute(
        self, api: pykube.HTTPClient, namespace: pykube.Namespace, name: str, spec: dict
    ) -> pykube.ConfigMap:
        resource = pykube.ConfigMap(
            api,
            {
                "apiVersion": pykube.ConfigMap.version,
                "kind": pykube.ConfigMap.kind,
                "metadata": {
                    "name": f"{name}-images",
                    "namespace": namespace.name,
                },
                "data": {
                    "values.yaml": yaml.dump(
                        {
                            "images": {
                                "tags": utils.generate_image_tags(
                                    spec["imageRepository"]
                                )
                            }
                        }
                    )
                },
            },
        )

        return self._apply(resource)


class GetChartValues(task.Task):
    def __init__(self, chart_name: str, chart_version: str):
        super().__init__(
            name=f"GetChartValues(chart_name={chart_name}, chart_version={chart_version})",
            inject={
                "chart_name": chart_name,
                "chart_version": chart_version,
            },
            provides=f"{chart_name}_chart_values",
        )

    def execute(
        self,
        helm_repository: HelmRepository,
        chart_name: str,
        chart_version: str,
    ) -> dict:
        # TODO(mnaser): Once we move towards air-gapped deployments, we should
        #               refactor this to pull from local OCI registry instead.
        subprocess.check_call(
            f"helm repo add --force-update {helm_repository.name} {helm_repository.obj['spec']['url']}",
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
            f"helm show values {helm_repository.name}/{chart_name} --version {chart_version}",
            shell=True,
        )
        return yaml.safe_load(data)


class GenerateOpenStackHelmReleaseValues(task.Task):
    def _generate_base(
        self,
        spec: dict,
        rabbitmq: RabbitmqCluster = None,
        percona_xtradb_cluster: PerconaXtraDBCluster = None,
    ) -> dict:
        values = {
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
                    "hosts": {},
                },
                "oslo_messaging": {
                    "statefulset": None,
                    "hosts": {},
                },
            },
        }

        if percona_xtradb_cluster:
            values["endpoints"]["oslo_db"]["hosts"] = {
                "default": f"{percona_xtradb_cluster.name}-haproxy",
            }

        if rabbitmq:
            values["endpoints"]["oslo_messaging"]["hosts"] = {
                "default": rabbitmq.name,
            }

        return values

    def _generate_memcached(self, **kwargs) -> dict:
        return {
            "monitoring": {
                "prometheus": {
                    "enabled": True,
                }
            }
        }

    def _generate_magnum(self, spec: dict) -> dict:
        return {
            # TODO(mnaser): This endpoints section should be automatically
            #               generated by the task.
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
            self._generate_base(spec),
            getattr(self, f"_generate_{chart_name}")(spec=spec),
            spec[chart_name].get("overrides", {}),
        )


class GenerateOpenStackHelmWithInfraReleaseValues(GenerateOpenStackHelmReleaseValues):
    def execute(
        self,
        chart_name: str,
        spec: dict,
        rabbitmq: RabbitmqCluster,
        percona_xtradb_cluster: PerconaXtraDBCluster,
    ) -> dict:
        return mergedeep.merge(
            {},
            self._generate_base(
                spec, rabbitmq=rabbitmq, percona_xtradb_cluster=percona_xtradb_cluster
            ),
            getattr(self, f"_generate_{chart_name}")(spec),
            spec[chart_name].get("overrides", {}),
        )


class GenerateOpenStackHelmValuesFrom(task.Task):
    SKIPPED_ENDPOINTS = set(
        [
            "cluster_domain_suffix",
            "container_infra",
            "fluentd",
            "key_manager",
            "kube_dns",
            "local_image_registry",
            "oci_image_registry",
            "orchestration",
        ]
    )

    def _generate_identity(
        self, chart_name: str, chart_values: dict, secrets: pykube.Secret, **kwargs
    ):
        values_from = [
            {
                "kind": pykube.Secret.kind,
                "name": secrets.name,
                "targetPath": "endpoints.identity.auth.admin.password",
                "valuesKey": "keystone-admin-password",
            },
        ]

        for service in chart_values["endpoints"]["identity"]["auth"]:
            if service == "admin":
                continue
            values_from += [
                {
                    "kind": pykube.Secret.kind,
                    "name": secrets.name,
                    "targetPath": f"endpoints.identity.auth.{service}.password",
                    "valuesKey": f"{service.replace('_', '-')}-keystone-password",
                },
            ]

        # NOTE(mnaser): This is workarounds for services which don't have all
        #               the endpoints defined properly.
        if chart_name == "magnum":
            values_from += [
                {
                    "kind": pykube.Secret.kind,
                    "name": secrets.name,
                    "targetPath": "conf.magnum.keystone_auth.password",
                    "valuesKey": "magnum-keystone-password",
                },
            ]

        return values_from

    def _generate_oslo_cache(self, secrets: pykube.Secret, **kwargs):
        return [
            {
                "kind": pykube.Secret.kind,
                "name": secrets.name,
                "targetPath": "endpoints.oslo_cache.auth.memcache_secret_key",
                "valuesKey": "memcache-secret-key",
            },
        ]

    def _generate_oslo_db(
        self,
        chart_values: dict,
        secrets: pykube.Secret,
        percona_xtradb_cluster: PerconaXtraDBCluster,
        **kwargs,
    ):
        values_from = [
            {
                "kind": pykube.Secret.kind,
                "name": percona_xtradb_cluster.name,
                "targetPath": "endpoints.oslo_db.auth.admin.password",
                "valuesKey": "root",
            },
        ]

        for service in chart_values["endpoints"]["oslo_db"]["auth"]:
            if service == "admin":
                continue
            values_from += [
                {
                    "kind": pykube.Secret.kind,
                    "name": secrets.name,
                    "targetPath": f"endpoints.oslo_db.auth.{service}.password",
                    "valuesKey": f"{service}-database-password",
                },
            ]

        return values_from

    def _generate_oslo_messaging(
        self,
        chart_values: dict,
        secrets: pykube.Secret,
        rabbitmq: RabbitmqCluster,
        **kwargs,
    ):
        values_from = [
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
        ]

        for service in chart_values["endpoints"]["oslo_messaging"]["auth"]:
            if service == "admin":
                continue
            values_from += [
                {
                    "kind": pykube.Secret.kind,
                    "name": secrets.name,
                    "targetPath": f"endpoints.oslo_messaging.auth.{service}.password",
                    "valuesKey": f"{service}-rabbitmq-password",
                },
            ]

        return values_from

    def execute(
        self,
        chart_name: str,
        chart_values: dict,
        image_tags: pykube.ConfigMap,
        secrets: pykube.Secret,
    ) -> dict:
        values_from = [
            {
                "kind": pykube.ConfigMap.kind,
                "name": image_tags.name,
            },
        ]

        for endpoint in chart_values["endpoints"]:
            if endpoint in self.SKIPPED_ENDPOINTS:
                continue
            values_from += getattr(self, f"_generate_{endpoint}")(
                chart_name=chart_name,
                chart_values=chart_values,
                secrets=secrets,
            )

        return values_from


class GenerateOpenStackHelmWithInfraValuesFrom(GenerateOpenStackHelmValuesFrom):
    def execute(
        self,
        chart_name: str,
        chart_values: dict,
        image_tags: pykube.ConfigMap,
        secrets: pykube.Secret,
        rabbitmq: RabbitmqCluster,
        percona_xtradb_cluster: PerconaXtraDBCluster,
    ) -> dict:
        values_from = [
            {
                "kind": pykube.ConfigMap.kind,
                "name": image_tags.name,
            },
        ]

        for endpoint in chart_values["endpoints"]:
            if endpoint in self.SKIPPED_ENDPOINTS:
                continue
            values_from += getattr(self, f"_generate_{endpoint}")(
                chart_name=chart_name,
                chart_values=chart_values,
                secrets=secrets,
                rabbitmq=rabbitmq,
                percona_xtradb_cluster=percona_xtradb_cluster,
            )

        return values_from


class ApplyIngressTask(ApplyKubernetesObjectTask):
    def execute(
        self,
        api: pykube.HTTPClient,
        namespace: pykube.Namespace,
        endpoint: str,
        spec: dict,
        chart_values: dict,
        helm_release: HelmRelease,
        cluster_issuer: ClusterIssuer,
    ) -> pykube.Ingress:
        release_values = helm_release.obj["spec"]["values"]
        host = release_values["endpoints"][endpoint]["host_fqdn_override"]["public"][
            "host"
        ]
        service_name = chart_values["endpoints"][endpoint]["hosts"]["default"]
        service_port = chart_values["endpoints"][endpoint]["port"]["api"]["default"]

        resource = pykube.Ingress(
            api,
            {
                "apiVersion": pykube.Ingress.version,
                "kind": pykube.Ingress.kind,
                "metadata": {
                    "name": endpoint.replace("_", "-"),
                    "namespace": namespace.name,
                    "annotations": {
                        "cert-manager.io/cluster-issuer": cluster_issuer.name,
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

        return self._apply(resource)
