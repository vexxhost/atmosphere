# Copyright (c) 2024 VEXXHOST, Inc.
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

import io
import json
import os
import subprocess

from oslo_log import log as logging
from taskflow import engines, task  # type: ignore
from taskflow.patterns import graph_flow as gf  # type: ignore
from taskflow.patterns import linear_flow as lf  # type: ignore

from atmosphere import exceptions

LOG = logging.getLogger(__name__)


class AnsiblePlaybookTask(task.Task):
    def __init__(
        self,
        inventory: str,
        playbook: str,
        tags: set[str] = set(),
        limit: set[str] = set(),
        **kwargs,
    ):
        super().__init__(
            "AnsiblePlaybookTask<Inventory: %s, Playbook: %s, Tags: %s, Limit: %s>"
            % (inventory, playbook, tags, limit),
            **kwargs,
        )

        self._inventory = inventory
        self._playbook = playbook
        self._tags = tags
        self._limit = limit

    def execute(self, *args, **kwargs):
        # TODO(mnaser): Switch to "ansible-runner"

        cmd = ["ansible-playbook", "-i", self._inventory, self._playbook]
        if self._tags:
            cmd += ["--tags", ",".join(self._tags)]
        if self._limit:
            cmd += ["--limit", ",".join(self._limit)]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            env={
                **os.environ,
                "PYTHONUNBUFFERED": "1",
                "ANSIBLE_FORCE_COLOR": "1",
                "ANSIBLE_STDOUT_CALLBACK": "ansible.posix.jsonl",
            },
        )
        for line in io.TextIOWrapper(process.stdout, encoding="utf-8"):
            data = json.loads(line)

            if data["_event"] in (
                "v2_playbook_on_handler_task_start",
                "v2_playbook_on_play_start",
                "v2_playbook_on_stats",
                "v2_playbook_on_task_start",
            ):
                continue

            if data["_event"].startswith("v2_runner_on_"):
                context = {
                    "playbook": self._playbook,
                }

                task_name = data["task"]["name"]
                if " : " in data["task"]["name"]:
                    context["role"], task_name = data["task"]["name"].split(" : ", 1)

                for host, result in data["hosts"].items():
                    context["host"] = host

                    if "skipped" in result:
                        context["skipped"] = result["skipped"]
                        LOG.info(
                            "%(task_name)s %(context)s",
                            {
                                "task_name": task_name,
                                "context": context,
                            },
                        )
                    elif "failed" in result:
                        context["failed"] = result["failed"]
                        context["msg"] = result["msg"]
                        LOG.error(
                            "%(task_name)s %(context)s",
                            {
                                "task_name": task_name,
                                "context": context,
                            },
                        )
                    elif "changed" in result:
                        context["changed"] = result["changed"]
                        LOG.info(
                            "%(task_name)s %(context)s",
                            {
                                "task_name": task_name,
                                "context": context,
                            },
                        )
            else:
                raise Exception("Unknown event: %s" % data["_event"])

        process.wait()
        if process.returncode != 0:
            raise exceptions.AnsiblePlaybookError(self._playbook)


def deploy(inventory: str, tags: set[str] = set(), limit: set[str] = set()):
    flow = gf.Flow("deploy").add(
        # Ceph
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.ceph",
            limit=limit,
            tags=tags,
            provides="ceph",
        ),
        # Kubernetes
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.kubernetes",
            limit=limit,
            tags=tags,
            provides="kubernetes",
        ),
        # CSI
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.csi",
            limit=limit,
            tags=tags,
            requires=["ceph", "kubernetes"],
            provides="csi",
        ),
        # Infrastructure
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.cert_manager",
            limit=limit,
            tags=tags,
            requires=["kubernetes"],
            provides="cert-manager",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.cluster_issuer",
            limit=limit,
            tags=tags,
            requires=["cert-manager"],
            provides="cluster-issuer",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.ingress_nginx",
            limit=limit,
            tags=tags,
            requires=["kubernetes"],
            provides="ingress-nginx",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.rabbitmq_cluster_operator",
            limit=limit,
            tags=tags,
            requires=["cert-manager"],
            provides="rabbitmq-cluster-operator",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.percona_xtradb_cluster_operator",
            limit=limit,
            tags=tags,
            requires=["kubernetes"],
            provides="percona-xtradb-cluster-operator",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.percona_xtradb_cluster",
            limit=limit,
            tags=tags,
            requires=["csi", "percona-xtradb-cluster-operator"],
            provides="percona-xtradb-cluster",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.keycloak",
            limit=limit,
            tags=tags,
            requires=["percona-xtradb-cluster"],
            provides="keycloak",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.keepalived",
            limit=limit,
            tags=tags,
            requires=["kubernetes"],
            provides="keepalived",
        ),
        # Monitoring
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.node_feature_discovery",
            limit=limit,
            tags=tags,
            requires=["kubernetes"],
            provides="node-feature-discovery",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.kube_prometheus_stack",
            limit=limit,
            tags=tags,
            requires=["kubernetes", "csi", "keycloak"],
            provides="kube-prometheus-stack",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.loki",
            limit=limit,
            tags=tags,
            requires=["kubernetes", "csi"],
            provides="loki",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.vector",
            limit=limit,
            tags=tags,
            requires=["kubernetes"],
            provides="vector",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.ipmi_exporter",
            limit=limit,
            tags=tags,
            requires=["kubernetes"],
            provides="ipmi-exporter",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.prometheus_pushgateway",
            limit=limit,
            tags=tags,
            requires=["kubernetes", "kube-prometheus-stack"],
            provides="prometheus-pushgateway",
        ),
        # OpenStack
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.memcached",
            limit=limit,
            tags=tags,
            requires=["kubernetes"],
            provides="memcached",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.keystone",
            limit=limit,
            tags=tags,
            requires=[
                "kubernetes",
                "keycloak",
                "rabbitmq-cluster-operator",
                "percona-xtradb-cluster",
                "memcached",
            ],
            provides="keystone",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.barbican",
            limit=limit,
            tags=tags,
            requires=["kubernetes", "percona-xtradb-cluster", "memcached", "keystone"],
            provides="barbican",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.rook_ceph",
            limit=limit,
            tags=tags,
            requires=["kubernetes"],
            provides="rook_ceph",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.rook_ceph_cluster",
            limit=limit,
            tags=tags,
            requires=["ceph", "kubernetes", "ingress-nginx", "keystone"],
            provides="rook_ceph_cluster",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.ceph_provisioners",
            limit=limit,
            tags=tags,
            requires=["ceph", "kubernetes"],
            provides="ceph_provisioners",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.glance",
            limit=limit,
            tags=tags,
            requires=[
                "kubernetes",
                "percona-xtradb-cluster",
                "memcached",
                "keystone",
                "ceph_provisioners",
            ],
            provides="glance",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.staffeln",
            limit=limit,
            tags=tags,
            requires=[
                "kubernetes",
                "percona-xtradb-cluster",
                "memcached",
                "keystone",
            ],
            provides="staffeln",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.cinder",
            limit=limit,
            tags=tags,
            requires=[
                "kubernetes",
                "percona-xtradb-cluster",
                "memcached",
                "keystone",
                "ceph_provisioners",
            ],
            provides="cinder",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.placement",
            limit=limit,
            tags=tags,
            requires=[
                "kubernetes",
                "percona-xtradb-cluster",
                "memcached",
                "keystone",
            ],
            provides="placement",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.lpfc",
            limit=limit,
            tags=tags,
            requires=[],
            provides="lpfc",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.multipathd",
            limit=limit,
            tags=tags,
            requires=[],
            provides="multipathd",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.openvswitch",
            limit=limit,
            tags=tags,
            requires=["kubernetes"],
            provides="openvswitch",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.ovn",
            limit=limit,
            tags=tags,
            requires=["kubernetes", "openvswitch"],
            provides="ovn",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.libvirt",
            limit=limit,
            tags=tags,
            requires=["kubernetes", "neutron"],
            provides="libvirt",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.coredns",
            limit=limit,
            tags=tags,
            requires=["kubernetes"],
            provides="coredns",
        ),
        lf.Flow("nova-and-neutron").add(
            AnsiblePlaybookTask(
                inventory,
                "vexxhost.atmosphere.nova",
                limit=limit,
                tags=tags,
                requires=[
                    "rabbitmq-cluster-operator",
                    "percona-xtradb-cluster",
                    "openvswitch",
                    "keystone",
                    "glance",
                ],
                provides="nova",
            ),
            AnsiblePlaybookTask(
                inventory,
                "vexxhost.atmosphere.neutron",
                limit=limit,
                tags=tags,
                requires=[
                    "rabbitmq-cluster-operator",
                    "percona-xtradb-cluster",
                    "openvswitch",
                    "keystone",
                    "coredns",
                    "ovn",
                ],
                provides="neutron",
            ),
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.senlin",
            limit=limit,
            tags=tags,
            requires=[
                "rabbitmq-cluster-operator",
                "percona-xtradb-cluster",
                "keystone",
            ],
            provides="senlin",
        ),
        # TODO(mnaser): Designate
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.heat",
            limit=limit,
            tags=tags,
            requires=[
                "rabbitmq-cluster-operator",
                "percona-xtradb-cluster",
                "keystone",
            ],
            provides="heat",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.octavia",
            limit=limit,
            tags=tags,
            requires=[
                "rabbitmq-cluster-operator",
                "percona-xtradb-cluster",
                "keystone",
                "glance",
                "neutron",
                "openstack_cli",
            ],
            provides="octavia",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.magnum",
            limit=limit,
            tags=tags,
            requires=[
                "rabbitmq-cluster-operator",
                "percona-xtradb-cluster",
                "keystone",
                "barbican",
                "heat",
            ],
            provides="magnum",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.manila",
            limit=limit,
            tags=tags,
            requires=[
                "rabbitmq-cluster-operator",
                "percona-xtradb-cluster",
                "keystone",
                "glance",
                "nova",
            ],
            provides="manila",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.horizon",
            limit=limit,
            tags=tags,
            requires=[
                "percona-xtradb-cluster",
                "keystone",
            ],
            provides="horizon",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.openstack_exporter",
            limit=limit,
            tags=tags,
            requires=[
                "keystone",
            ],
            provides="openstack_exporter",
        ),
        AnsiblePlaybookTask(
            inventory,
            "vexxhost.atmosphere.openstack_cli",
            limit=limit,
            tags=tags,
            requires=[
                "keystone",
            ],
            provides="openstack_cli",
        ),
    )

    e = engines.load(flow, executor="threaded", engine="parallel", max_workers=8)
    e.run()
