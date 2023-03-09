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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.plugins.become import sudo

DOCUMENTATION = """
    name: sudo_netns
    short_description: Run inside a network namespace with `sudo`
    description:
        - This become plugin allows you to run commands inside a network
          namespace with `sudo`.
    author: VEXXHOST, Inc.
    version_added: "1.0.2"
    options:
        become_user:
            description: User you 'become' to execute the task
            default: root
            ini:
              - section: privilege_escalation
                key: become_user
              - section: sudo_become_plugin
                key: user
            vars:
              - name: ansible_become_user
              - name: ansible_sudo_user
            env:
              - name: ANSIBLE_BECOME_USER
              - name: ANSIBLE_SUDO_USER
            keyword:
              - name: become_user
        become_netns:
            description: Network namespace
            required: true
            default: sudo
            keyword:
              - name: become_netns
"""


class BecomeModule(sudo.BecomeModule):
    def _build_success_command(self, *args, **kwargs):
        return "ip netns exec %s %s" % (
            self.get_option("become_netns"),
            super(BecomeModule, self)._build_success_command(*args, **kwargs),
        )
