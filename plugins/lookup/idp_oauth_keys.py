# Copyright (c) 2025 VEXXHOST, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License


from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import requests
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        keystone_domains = terms[0]
        validate_certs = kwargs.get("validate_certs", True)
        validate_certs = validate_certs != "Off"

        if not isinstance(keystone_domains, list):
            raise AnsibleError("Expected a list of keystone domains.")

        result = {}

        for domain in keystone_domains:
            try:
                domain_name = domain["name"]
                url, realm = domain["keycloak_server_url"], domain["keycloak_realm"]
                well_known_url = (
                    f"{url}/realms/{realm}/.well-known/openid-configuration"
                )
                # Fetch OpenID configuration
                response = requests.get(well_known_url, verify=validate_certs)
                response.raise_for_status()
                openid_config = response.json()

                # Fetch JWKS URI
                jwks_uri = openid_config.get("jwks_uri")
                if not jwks_uri:
                    raise AnsibleError(
                        f"No 'jwks_uri' found in OpenID config for domain {domain_name}"
                    )

                jwks_response = requests.get(jwks_uri, verify=validate_certs)
                jwks_response.raise_for_status()
                jwks_data = jwks_response.json()

                # Extract 'kid' for signing keys
                kid_list = [
                    key["kid"]
                    for key in jwks_data.get("keys", [])
                    if key.get("use") == "sig"
                ]
                if not kid_list:
                    raise AnsibleError(
                        f"No signing keys found for domain {domain_name}"
                    )

                kid_cert_list = [
                    key["x5c"][0]
                    for key in jwks_data.get("keys", [])
                    if key.get("use") == "sig"
                ]
                if not kid_cert_list:
                    raise AnsibleError(
                        f"No signing cert found for domain {domain_name}"
                    )

                # for keycloak, there is only one signing key id and x509 certificate
                result[domain_name] = {
                    "idp_oauth_kid_cert": kid_cert_list[0],
                    "idp_oauth_kid": kid_list[0],
                    "idp_oauth_kid_cert_path": f"{kid_list[0]}#/var/lib/apache2/oauth_certs/{kid_list[0]}.pem",
                }

            except requests.exceptions.RequestException as e:
                raise AnsibleError(
                    f"Request failed from IDP for domain {domain_name}: {str(e)}"
                )
            except (KeyError, json.JSONDecodeError) as e:
                raise AnsibleError(
                    f"Error processing IDP cert data for domain {domain_name}: {str(e)}"
                )

        return [result]
