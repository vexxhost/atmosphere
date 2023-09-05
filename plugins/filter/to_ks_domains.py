# Copyright (c) 2022 VEXXHOST, Inc.
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
# under the License.


def to_ks_domain(domain):
    return {
        "identity": {"driver": "keycloak"},
        "keycloak": {
            "server_url": domain["keycloak_server_internal_url"],
            "user_realm_name": domain["keycloak_user_realm_name"],
            "client_id": domain["keycloak_admin_client_id"],
            "username": domain["keycloak_admin_user"],
            "password": domain["keycloak_admin_password"],
            "realm_name": domain["keycloak_realm"],
        },
    }


def to_ks_domains(domains):
    return {d["name"]: to_ks_domain(d) for d in domains}


class FilterModule(object):
    def filters(self):
        return {"to_ks_domains": to_ks_domains}
