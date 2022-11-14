import textwrap

import pykube
import pytest

from atmosphere.models import config
from atmosphere.tasks import constants
from atmosphere.tasks.kubernetes import cert_manager


@pytest.mark.parametrize(
    "cfg_data,expected",
    [
        pytest.param(
            textwrap.dedent(
                """\
                [issuer]
                email = "mnaser@vexxhost.com"
                """
            ),
            [
                {
                    "apiVersion": cert_manager.Issuer.version,
                    "kind": cert_manager.Issuer.kind,
                    "metadata": {
                        "name": "self-signed",
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "spec": {
                        "selfSigned": {},
                    },
                },
                {
                    "apiVersion": cert_manager.Issuer.version,
                    "kind": cert_manager.Issuer.kind,
                    "metadata": {
                        "name": "openstack",
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "spec": {
                        "acme": {
                            "email": "mnaser@vexxhost.com",
                            "server": "https://acme-v02.api.letsencrypt.org/directory",
                            "privateKeySecretRef": {
                                "name": "cert-manager-issuer-account-key",
                            },
                            "solvers": [
                                {
                                    "http01": {
                                        "ingress": {
                                            "class": "openstack",
                                        },
                                    },
                                },
                            ],
                        },
                    },
                },
            ],
            id="default",
        ),
        pytest.param(
            textwrap.dedent(
                """\
                [issuer]
                email = "mnaser@vexxhost.com"

                [issuer.solver]
                type = "rfc2136"
                nameserver = "1.2.3.4:53"
                tsig_algorithm = "hmac-sha256"
                tsig_key_name = "foobar"
                tsig_secret = "secret123"
                """
            ),
            [
                {
                    "apiVersion": cert_manager.Issuer.version,
                    "kind": cert_manager.Issuer.kind,
                    "metadata": {
                        "name": "self-signed",
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "spec": {
                        "selfSigned": {},
                    },
                },
                {
                    "apiVersion": pykube.Secret.version,
                    "kind": pykube.Secret.kind,
                    "metadata": {
                        "name": "cert-manager-issuer-tsig-secret-key",
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "stringData": {
                        "tsig-secret-key": "secret123",
                    },
                },
                {
                    "apiVersion": cert_manager.Issuer.version,
                    "kind": cert_manager.Issuer.kind,
                    "metadata": {
                        "name": "openstack",
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "spec": {
                        "acme": {
                            "email": "mnaser@vexxhost.com",
                            "server": "https://acme-v02.api.letsencrypt.org/directory",
                            "privateKeySecretRef": {
                                "name": "cert-manager-issuer-account-key",
                            },
                            "solvers": [
                                {
                                    "dns01": {
                                        "rfc2136": {
                                            "nameserver": "1.2.3.4:53",
                                            "tsigAlgorithm": "hmac-sha256",
                                            "tsigKeyName": "foobar",
                                            "tsigSecretSecretRef": {
                                                "name": "cert-manager-issuer-tsig-secret-key",
                                                "key": "tsig-secret-key",
                                            },
                                        },
                                    },
                                },
                            ],
                        },
                    },
                },
            ],
            id="rfc2136",
        ),
        pytest.param(
            textwrap.dedent(
                """\
                [issuer]
                email = "mnaser@vexxhost.com"

                [issuer.solver]
                type = "route53"
                hosted_zone_id = "Z3A4X2Y2Y3"
                access_key_id = "AKIAIOSFODNN7EXAMPLE"
                secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                """
            ),
            [
                {
                    "apiVersion": cert_manager.Issuer.version,
                    "kind": cert_manager.Issuer.kind,
                    "metadata": {
                        "name": "self-signed",
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "spec": {
                        "selfSigned": {},
                    },
                },
                {
                    "apiVersion": pykube.Secret.version,
                    "kind": pykube.Secret.kind,
                    "metadata": {
                        "name": "cert-manager-issuer-route53-credentials",
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "stringData": {
                        "secret-access-key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                    },
                },
                {
                    "apiVersion": cert_manager.Issuer.version,
                    "kind": cert_manager.Issuer.kind,
                    "metadata": {
                        "name": "openstack",
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "spec": {
                        "acme": {
                            "email": "mnaser@vexxhost.com",
                            "server": "https://acme-v02.api.letsencrypt.org/directory",
                            "privateKeySecretRef": {
                                "name": "cert-manager-issuer-account-key",
                            },
                            "solvers": [
                                {
                                    "dns01": {
                                        "route53": {
                                            "region": "global",
                                            "hostedZoneID": "Z3A4X2Y2Y3",
                                            "accessKeyID": "AKIAIOSFODNN7EXAMPLE",
                                            "secretAccessKeySecretRef": {
                                                "name": "cert-manager-issuer-route53-credentials",
                                                "key": "secret-access-key",
                                            },
                                        },
                                    },
                                },
                            ],
                        },
                    },
                },
            ],
            id="route53",
        ),
        pytest.param(
            textwrap.dedent(
                """\
                [issuer]
                type = "ca"
                certificate = '''
                -----BEGIN CERTIFICATE-----
                MIIDBjCCAe4CCQDQ3Z0Z2Z0Z0jANBgkqhkiG9w0BAQsFADCBhTELMAkGA1UEBhMC
                VVMxEzARBgNVBAgTCkNhbGlmb3JuaWExFjAUBgNVBAcTDVNhbiBGcmFuY2lzY28x
                ...
                -----END CERTIFICATE-----
                '''
                private_key = '''
                -----BEGIN RSA PRIVATE KEY-----
                MIIEpAIBAAKCAQEAw3Z0Z2Z0Z0jANBgkqhkiG9w0BAQsFADCBhTELMAkGA1UEBhMC
                VVMxEzARBgNVBAgTCkNhbGlmb3JuaWExFjAUBgNVBAcTDVNhbiBGcmFuY2lzY28x
                ...
                -----END RSA PRIVATE KEY-----
                '''
                """
            ),
            [
                {
                    "apiVersion": cert_manager.Issuer.version,
                    "kind": cert_manager.Issuer.kind,
                    "metadata": {
                        "name": "self-signed",
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "spec": {
                        "selfSigned": {},
                    },
                },
                {
                    "apiVersion": pykube.Secret.version,
                    "kind": pykube.Secret.kind,
                    "metadata": {
                        "name": "cert-manager-issuer-ca",
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "stringData": {
                        "tls.crt": textwrap.dedent(
                            """\
                            -----BEGIN CERTIFICATE-----
                            MIIDBjCCAe4CCQDQ3Z0Z2Z0Z0jANBgkqhkiG9w0BAQsFADCBhTELMAkGA1UEBhMC
                            VVMxEzARBgNVBAgTCkNhbGlmb3JuaWExFjAUBgNVBAcTDVNhbiBGcmFuY2lzY28x
                            ...
                            -----END CERTIFICATE-----
                            """
                        ),
                        "tls.key": textwrap.dedent(
                            """\
                            -----BEGIN RSA PRIVATE KEY-----
                            MIIEpAIBAAKCAQEAw3Z0Z2Z0Z0jANBgkqhkiG9w0BAQsFADCBhTELMAkGA1UEBhMC
                            VVMxEzARBgNVBAgTCkNhbGlmb3JuaWExFjAUBgNVBAcTDVNhbiBGcmFuY2lzY28x
                            ...
                            -----END RSA PRIVATE KEY-----
                            """
                        ),
                    },
                },
                {
                    "apiVersion": cert_manager.Issuer.version,
                    "kind": cert_manager.Issuer.kind,
                    "metadata": {
                        "name": "openstack",
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "spec": {
                        "ca": {
                            "secretName": "cert-manager-issuer-ca",
                        },
                    },
                },
            ],
            id="ca",
        ),
        pytest.param(
            textwrap.dedent(
                """\
                [issuer]
                type = "self-signed"
                """
            ),
            [
                {
                    "apiVersion": cert_manager.Issuer.version,
                    "kind": cert_manager.Issuer.kind,
                    "metadata": {
                        "name": "self-signed",
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "spec": {
                        "selfSigned": {},
                    },
                },
                {
                    "apiVersion": cert_manager.Certificate.version,
                    "kind": cert_manager.Certificate.kind,
                    "metadata": {
                        "name": "self-signed-ca",
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "spec": {
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
                },
                {
                    "apiVersion": cert_manager.Issuer.version,
                    "kind": cert_manager.Issuer.kind,
                    "metadata": {
                        "name": "openstack",
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "spec": {
                        "ca": {
                            "secretName": "cert-manager-selfsigned-ca",
                        },
                    },
                },
            ],
            id="self-signed",
        ),
    ],
)
def test_apply_issuer_task_from_config(pykube, cfg_data, expected):
    cfg = config.Config.from_string(cfg_data, validate=False)
    cfg.issuer.validate()
    assert [
        t.generate_object().obj
        for t in cert_manager.issuer_tasks_from_config(cfg.issuer)
    ] == expected
