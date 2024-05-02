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

import os
from datetime import datetime, timedelta

import testscenarios  # type: ignore
from kubernetes import client, config  # type: ignore
from kubernetes.stream import stream  # type: ignore
from oslotest import base  # type: ignore
from testtools import matchers, testcase  # type: ignore

config.load_kube_config()


class TestOVN(testscenarios.WithScenarios, testcase.WithAttributes, base.BaseTestCase):
    scenarios = [
        ("ovsdb-nb", {"statefulset": "ovn-ovsdb-nb", "filename": "ovnnb_db.db"}),
        ("ovsdb-sb", {"statefulset": "ovn-ovsdb-sb", "filename": "ovnsb_db.db"}),
    ]

    def setUp(self):
        super(TestOVN, self).setUp()

        self.corev1 = client.CoreV1Api()
        self.appsv1 = client.AppsV1Api()

        if os.environ["ATMOSPHERE_NETWORK_BACKEND"] != "ovn":
            self.skipTest("OVN is not deployed on this cloud.")

    def _read_stateful_set(self):
        return self.appsv1.read_namespaced_stateful_set(
            name=self.statefulset, namespace="openstack"
        )

    def test_ovn_is_running(self):
        sts = self._read_stateful_set()
        self.assertEqual(sts.spec.replicas, sts.status.replicas)

    def test_ovn_is_using_correct_database_folder(self):
        sts = self._read_stateful_set()
        self.assertThat(sts.spec.volume_claim_templates, matchers.HasLength(1))
        self.assertEqual(sts.spec.volume_claim_templates[0].metadata.name, "data")

        volume_mounts = sts.spec.template.spec.containers[0].volume_mounts
        volume_mount = next(
            (
                vm
                for vm in volume_mounts
                if vm.name == sts.spec.volume_claim_templates[0].metadata.name
            )
        )

        self.assertEqual(volume_mount.mount_path, "/etc/ovn")

        db_last_modified = stream(
            self.corev1.connect_get_namespaced_pod_exec,
            f"{sts.metadata.name}-0",
            sts.metadata.namespace,
            command=["stat", "-c", "%Y", f"{volume_mount.mount_path}/{self.filename}"],
            stdin=False,
            stderr=True,
            stdout=True,
            tty=False,
        )

        db_last_modified = datetime.fromtimestamp(int(db_last_modified))
        self.assertTrue(db_last_modified > datetime.now() - timedelta(minutes=5))
