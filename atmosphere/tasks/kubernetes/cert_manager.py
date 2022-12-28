import pykube

from atmosphere.models import config
from atmosphere.operator import tasks
from atmosphere.tasks import constants
from atmosphere.tasks.kubernetes import base


class Certificate(pykube.objects.NamespacedAPIObject):
    version = "cert-manager.io/v1"
    endpoint = "certificates"
    kind = "Certificate"


class ApplyCertificateTask(base.ApplyKubernetesObjectTask):
    def __init__(self, namespace: str, name: str, spec: dict):
        self._spec = spec

        super().__init__(
            kind=Certificate,
            namespace=namespace,
            name=name,
            requires=set(
                [
                    f"helm-release-{constants.NAMESPACE_CERT_MANAGER}-{constants.HELM_RELEASE_CERT_MANAGER_NAME}",
                ]
            ),
        )

    def generate_object(self) -> Certificate:
        return Certificate(
            self.api,
            {
                "apiVersion": self._obj_kind.version,
                "kind": self._obj_kind.kind,
                "metadata": {
                    "name": self._obj_name,
                    "namespace": self._obj_namespace,
                },
                "spec": self._spec,
            },
        )


class ClusterIssuer(pykube.objects.APIObject):
    version = "cert-manager.io/v1"
    endpoint = "clusterissuers"
    kind = "ClusterIssuer"


class ApplyClusterIssuerTask(base.ApplyKubernetesObjectTask):
    def __init__(self, name: str, spec: dict):
        self._spec = spec

        super().__init__(
            kind=ClusterIssuer,
            namespace=None,
            name=name,
            requires=set(["cert_manager_helm_release"]),
        )

    def generate_object(self) -> ClusterIssuer:
        return ClusterIssuer(
            self.api,
            {
                "apiVersion": self._obj_kind.version,
                "kind": self._obj_kind.kind,
                "metadata": {
                    "name": self._obj_name,
                },
                "spec": self._spec,
            },
        )


def issuer_tasks_from_config(config: config.Issuer) -> list:
    objects = [
        ApplyClusterIssuerTask(
            name="self-signed",
            spec={
                "selfSigned": {},
            },
        )
    ]

    if config.type == "acme":
        spec = {
            "acme": {
                "email": config.email,
                "server": config.server,
                "privateKeySecretRef": {
                    "name": "cert-manager-issuer-account-key",
                },
            },
        }

        if config.solver.type == "http":
            spec["acme"]["solvers"] = [
                {
                    "http01": {
                        "ingress": {
                            "class": "openstack",
                        },
                    },
                },
            ]
        elif config.solver.type == "rfc2136":
            # NOTE(mnaser): We have to create a secret containing the AWS
            #               credentials in this case.
            objects.append(
                tasks.ApplySecretTask(
                    "cert-manager-issuer-tsig-secret-key",
                    inject={
                        "data": {
                            "tsig-secret-key": config.solver.tsig_secret,
                        },
                    },
                    rebind={
                        "namespace": "cert_manager_namespace",
                    },
                )
            )

            spec["acme"]["solvers"] = [
                {
                    "dns01": {
                        "rfc2136": {
                            "nameserver": config.solver.nameserver,
                            "tsigAlgorithm": config.solver.tsig_algorithm,
                            "tsigKeyName": config.solver.tsig_key_name,
                            "tsigSecretSecretRef": {
                                "name": "cert-manager-issuer-tsig-secret-key",
                                "key": "tsig-secret-key",
                            },
                        },
                    },
                },
            ]
        elif config.solver.type == "route53":
            # NOTE(mnaser): We have to create a secret containing the AWS
            #               credentials in this case.
            objects.append(
                tasks.ApplySecretTask(
                    "cert-manager-issuer-route53-credentials",
                    inject={
                        "data": {"secret-access-key": config.solver.secret_access_key},
                    },
                    rebind={
                        "namespace": "cert_manager_namespace",
                    },
                )
            )

            spec["acme"]["solvers"] = [
                {
                    "dns01": {
                        "route53": {
                            "region": config.solver.region,
                            "hostedZoneID": config.solver.hosted_zone_id,
                            "accessKeyID": config.solver.access_key_id,
                            "secretAccessKeySecretRef": {
                                "name": "cert-manager-issuer-route53-credentials",
                                "key": "secret-access-key",
                            },
                        },
                    },
                },
            ]
    elif config.type == "ca":
        # NOTE(mnaser): We have to create a secret containing the CA
        #               certificate and key in this case.
        objects.append(
            tasks.ApplySecretTask(
                "cert-manager-issuer-ca",
                inject={
                    "data": {
                        "tls.crt": config.certificate,
                        "tls.key": config.private_key,
                    },
                },
                rebind={
                    "namespace": "cert_manager_namespace",
                },
            )
        )

        spec = {
            "ca": {
                "secretName": "cert-manager-issuer-ca",
            }
        }
    elif config.type == "self-signed":
        # NOTE(mnaser): We have to setup the self-signed CA in this case
        objects += [
            ApplyCertificateTask(
                namespace=constants.NAMESPACE_CERT_MANAGER,
                name="self-signed-ca",
                spec={
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
            ),
        ]

        spec = {
            "ca": {
                "secretName": "cert-manager-selfsigned-ca",
            }
        }

    return objects + [ApplyClusterIssuerTask(name="atmosphere", spec=spec)]
