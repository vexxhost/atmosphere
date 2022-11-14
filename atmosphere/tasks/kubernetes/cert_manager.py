import pykube

from atmosphere.models import config
from atmosphere.tasks import constants
from atmosphere.tasks.kubernetes import base, v1


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


class Issuer(pykube.objects.NamespacedAPIObject):
    version = "cert-manager.io/v1"
    endpoint = "issuers"
    kind = "Issuer"


class ApplyIssuerTask(base.ApplyKubernetesObjectTask):
    def __init__(self, namespace: str, name: str, spec: dict):
        self._spec = spec

        super().__init__(
            kind=Issuer,
            namespace=namespace,
            name=name,
            requires=set(
                [
                    f"helm-release-{constants.NAMESPACE_CERT_MANAGER}-{constants.HELM_RELEASE_CERT_MANAGER_NAME}",
                ]
            ),
        )

    def generate_object(self) -> Issuer:
        return Issuer(
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


def issuer_tasks_from_config(config: config.Issuer) -> list:
    objects = [
        ApplyIssuerTask(
            namespace=constants.NAMESPACE_OPENSTACK,
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
                v1.ApplySecretTask(
                    constants.NAMESPACE_OPENSTACK,
                    "cert-manager-issuer-tsig-secret-key",
                    data={
                        "tsig-secret-key": config.solver.tsig_secret,
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
                v1.ApplySecretTask(
                    constants.NAMESPACE_OPENSTACK,
                    "cert-manager-issuer-route53-credentials",
                    data={
                        "secret-access-key": config.solver.secret_access_key,
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
            v1.ApplySecretTask(
                constants.NAMESPACE_OPENSTACK,
                "cert-manager-issuer-ca",
                data={
                    "tls.crt": config.certificate,
                    "tls.key": config.private_key,
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
                namespace=constants.NAMESPACE_OPENSTACK,
                name="self-signed-ca",
                spec={
                    "isCA": True,
                    "commonName": "selfsigned-ca",
                    "secretName": "cert-manager-selfsigned-ca",
                    "duration": "86400h",
                    "renewBefore": "360h",
                    "privateKey": {"algorithm": "ECDSA", "size": 256},
                    "issuerRef": {
                        "kind": "Issuer",
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

    return objects + [
        ApplyIssuerTask(
            namespace=constants.NAMESPACE_OPENSTACK, name="openstack", spec=spec
        )
    ]
