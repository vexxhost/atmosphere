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

from ansible.plugins.action import ActionBase
from ansible.template import Templar


class OpenStackActionBase(ActionBase):
    def run(self, tmp=None, task_vars=None):
        super(OpenStackActionBase, self).run(tmp, task_vars)

        templar = Templar(loader=self._loader, variables=task_vars)

        keystone_api_host = templar.template(
            task_vars.get("openstack_helm_endpoints_keystone_api_host")
        )
        region_name = templar.template(
            task_vars.get("openstack_helm_endpoints_region_name")
        )
        admin_password = templar.template(
            task_vars.get("openstack_helm_endpoints_keystone_admin_password")
        )
        validate_certs = bool(
            templar.template("{{ cluster_issuer_type != 'self-signed' }}")
        )

        module_args = self._task.args.copy()
        openstack_args = {
            "auth": {
                "auth_url": f"https://{keystone_api_host}/v3",
                "user_domain_name": "Default",
                "username": f"admin-{region_name}",
                "password": admin_password,
                "project_domain_name": "Default",
                "project_name": "admin",
            },
            "region_name": region_name,
            "validate_certs": validate_certs,
        }

        return super(OpenStackActionBase, self)._execute_module(
            module_name=self._task.action.replace(
                "vexxhost.atmosphere", "openstack.cloud"
            ),
            module_args={**openstack_args, **module_args},
            task_vars=task_vars,
            tmp=tmp,
        )
