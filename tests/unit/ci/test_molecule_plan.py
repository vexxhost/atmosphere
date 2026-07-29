# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import re
from pathlib import Path

import pytest
import yaml

from atmosphere.ci.molecule_plan import (
    Change,
    Planner,
    PolicyError,
    parse_changes,
    render_plan,
)

POLICY_PATH = Path(__file__).parents[3] / "ci" / "molecule-plan.yaml"


@pytest.fixture
def planner() -> Planner:
    return Planner.load(POLICY_PATH)


def plan_path(planner: Planner, path: str) -> dict:
    return planner.plan([Change(status="M", path=path)])


def components(plan: dict, job: str = "aio-openvswitch") -> set[str]:
    return set(plan["job_decisions"][job]["components"])


def test_policy_is_valid(planner: Planner) -> None:
    assert planner.policy["version"] == 1


def test_keystone_uses_small_sequential_closure(planner: Planner) -> None:
    plan = plan_path(planner, "roles/keystone/tasks/main.yml")

    assert plan["mode"] == "selective"
    assert plan["targets"] == ["keystone"]
    assert plan["job_decisions"]["aio-openvswitch"]["run"] is True
    assert components(plan) >= {
        "ceph",
        "cluster-issuer",
        "csi",
        "keycloak",
        "keystone",
        "kubernetes",
        "percona-xtradb-cluster",
    }
    assert components(plan).isdisjoint(
        {"glance", "magnum", "manila", "neutron", "nova"}
    )


def test_glance_includes_storage_and_identity_only(
    planner: Planner,
) -> None:
    plan = plan_path(planner, "charts/glance/templates/deployment-api.yaml")
    decision = plan["job_decisions"]["aio-openvswitch"]

    assert components(plan) >= {
        "ceph",
        "ceph-provisioners",
        "glance",
        "keystone",
    }
    assert components(plan).isdisjoint(
        {"cinder", "heat", "magnum", "manila", "neutron", "nova"}
    )
    assert decision["tempest_tests"] == [r"^tempest\.api\.image\."]


def test_manila_includes_functional_dependencies(
    planner: Planner,
) -> None:
    plan = plan_path(planner, "charts/patches/manila/0001-example.patch")
    decision = plan["job_decisions"]["aio-openvswitch"]

    assert components(plan) >= {
        "ceph",
        "cinder",
        "glance",
        "keystone",
        "manila",
        "neutron",
        "nova",
        "placement",
    }
    assert components(plan).isdisjoint(
        {"heat", "horizon", "magnum", "openstack-exporter"}
    )
    assert decision["tempest_tests"] == []
    assert decision["run_tempest"] is False
    assert decision["verification_checks"] == [
        {"service": "shared_file_system", "type": "share"}
    ]


def test_unmapped_tempest_target_disables_filter_for_combined_change(
    planner: Planner,
) -> None:
    plan = planner.plan(
        [
            Change(status="M", path="roles/glance/tasks/main.yml"),
            Change(status="M", path="roles/openstack_cli/tasks/main.yml"),
        ]
    )

    assert plan["job_decisions"]["aio-openvswitch"]["tempest_tests"] == []
    assert plan["job_decisions"]["aio-openvswitch"]["run_tempest"] is True


def test_api_check_keeps_mapped_tempest_filter_for_combined_change(
    planner: Planner,
) -> None:
    plan = planner.plan(
        [
            Change(status="M", path="roles/glance/tasks/main.yml"),
            Change(status="M", path="roles/manila/tasks/main.yml"),
        ]
    )
    decision = plan["job_decisions"]["aio-openvswitch"]

    assert decision["tempest_tests"] == [r"^tempest\.api\.image\."]
    assert decision["run_tempest"] is True
    assert decision["verification_checks"] == [
        {"service": "shared_file_system", "type": "share"}
    ]


@pytest.mark.parametrize(
    ("role", "service", "resource_type"),
    [
        ("barbican", "key_manager", "secret"),
        ("placement", "placement", "resource_provider"),
        ("heat", "orchestration", "stack"),
        ("magnum", "container_infrastructure_management", "cluster"),
        ("manila", "shared_file_system", "share"),
    ],
)
def test_service_without_tempest_plugin_uses_read_only_api_check(
    planner: Planner,
    role: str,
    service: str,
    resource_type: str,
) -> None:
    plan = plan_path(
        planner,
        f"roles/{role}/tasks/main.yml",
    )
    decision = plan["job_decisions"]["aio-openvswitch"]

    assert decision["run_tempest"] is False
    assert decision["tempest_tests"] == []
    assert decision["verification_checks"] == [
        {"service": service, "type": resource_type}
    ]


def test_magnum_uses_broad_openstack_environment(
    planner: Planner,
) -> None:
    plan = plan_path(planner, "roles/magnum/tasks/main.yml")

    assert components(plan) >= {
        "barbican",
        "cinder",
        "glance",
        "heat",
        "magnum",
        "neutron",
        "nova",
        "octavia",
    }
    assert components(plan).isdisjoint({"horizon", "manila", "openstack-exporter"})


def test_horizon_includes_compute_for_dashboard_login(
    planner: Planner,
) -> None:
    plan = plan_path(planner, "roles/horizon/tasks/main.yml")

    assert components(plan) >= {
        "glance",
        "horizon",
        "keystone",
        "neutron",
        "nova",
        "placement",
    }


def test_nova_adds_neutron_as_a_functional_test_requirement(
    planner: Planner,
) -> None:
    plan = plan_path(planner, "roles/nova/tasks/main.yml")

    assert components(plan) >= {
        "coredns",
        "glance",
        "neutron",
        "nova",
        "openvswitch",
        "placement",
    }


def test_cinder_adds_glance_as_a_functional_test_requirement(
    planner: Planner,
) -> None:
    plan = plan_path(planner, "roles/cinder/tasks/main.yml")

    assert components(plan) >= {
        "ceph-provisioners",
        "cinder",
        "glance",
        "keystone",
    }


def test_neutron_creates_backend_specific_jobs(
    planner: Planner,
) -> None:
    plan = plan_path(planner, "roles/neutron/tasks/main.yml")
    ovs = plan["job_decisions"]["aio-openvswitch"]
    ovn = plan["job_decisions"]["aio-ovn"]

    assert ovs["run"] is True
    assert ovn["run"] is True
    assert "coredns" in ovs["components"]
    assert "ovn" not in ovs["components"]
    assert "ovn" in ovn["components"]
    assert "coredns" not in ovn["components"]
    assert ovs["tempest_tests"] == ovn["tempest_tests"]
    assert r"^neutron_tempest_plugin\." in ovs["tempest_tests"]


def test_csi_provider_paths_select_only_related_scenario(
    planner: Planner,
) -> None:
    local = plan_path(planner, "roles/local_path_provisioner/tasks/main.yml")
    rbd = plan_path(planner, "roles/ceph_csi_rbd/tasks/main.yml")

    assert local["job_decisions"]["csi-local-path-provisioner"]["run"]
    assert not local["job_decisions"]["csi-rbd"]["run"]
    assert not local["job_decisions"]["aio-openvswitch"]["run"]
    assert rbd["job_decisions"]["csi-rbd"]["run"]
    assert not rbd["job_decisions"]["csi-local-path-provisioner"]["run"]


def test_keycloak_change_uses_focused_scenario(
    planner: Planner,
) -> None:
    plan = plan_path(planner, "charts/keycloak/templates/statefulset.yaml")

    assert plan["job_decisions"]["keycloak"]["run"]
    assert not plan["job_decisions"]["aio-openvswitch"]["run"]
    assert not plan["job_decisions"]["aio-ovn"]["run"]


def test_ignored_path_is_noop(planner: Planner) -> None:
    plan = plan_path(planner, "doc/source/deploy/index.rst")

    assert plan["mode"] == "noop"
    assert not any(decision["run"] for decision in plan["job_decisions"].values())


def test_unknown_runtime_path_falls_back_to_every_job(
    planner: Planner,
) -> None:
    plan = plan_path(planner, "new-runtime-area/config.yaml")

    assert plan["mode"] == "full"
    assert all(decision["run"] for decision in plan["job_decisions"].values())
    expected_checks = {
        ("container_infrastructure_management", "cluster"),
        ("key_manager", "secret"),
        ("load_balancer", "load_balancer"),
        ("orchestration", "stack"),
        ("placement", "resource_provider"),
        ("shared_file_system", "share"),
    }
    for job_name in ("aio-openvswitch", "aio-ovn"):
        assert {
            (check["service"], check["type"])
            for check in plan["job_decisions"][job_name]["verification_checks"]
        } == expected_checks
    assert plan["job_decisions"]["csi-rbd"]["verification_checks"] == []


def test_empty_change_list_falls_back_to_every_job(
    planner: Planner,
) -> None:
    plan = planner.plan([])

    assert plan["mode"] == "full"
    assert all(decision["run"] for decision in plan["job_decisions"].values())


def test_rename_evaluates_old_and_new_paths(planner: Planner) -> None:
    plan = planner.plan(
        [
            Change(
                status="R100",
                previous_path="roles/keystone/tasks/old.yml",
                path="roles/manila/tasks/new.yml",
            )
        ]
    )

    assert plan["targets"] == ["keystone", "manila"]


def test_parse_name_status_preserves_rename() -> None:
    changes = parse_changes(
        [
            "M\troles/keystone/tasks/main.yml\n",
            "R100\troles/manila/tasks/old.yml\t" "roles/manila/tasks/new.yml\n",
        ]
    )

    assert len(changes) == 2
    assert changes[1].previous_path == "roles/manila/tasks/old.yml"


def test_component_graph_cycle_is_rejected() -> None:
    policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    invalid = copy.deepcopy(policy)
    invalid["components"]["ceph"]["requires"] = ["keystone"]

    with pytest.raises(PolicyError, match="cycle"):
        Planner(invalid)


def test_duplicate_policy_values_are_rejected() -> None:
    policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    invalid = copy.deepcopy(policy)
    invalid["components"]["csi"]["jobs"].append("csi-rbd")

    with pytest.raises(
        PolicyError,
        match=r"components\.csi\.jobs contains duplicate values: csi-rbd",
    ):
        Planner(invalid)


def test_malformed_tempest_test_patterns_are_rejected() -> None:
    policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    invalid = copy.deepcopy(policy)
    invalid["components"]["keystone"]["tempest_tests"] = "tempest.api.identity"

    with pytest.raises(
        PolicyError,
        match=r"components\.keystone\.tempest_tests must be a list of strings",
    ):
        Planner(invalid)


def test_invalid_tempest_test_regular_expression_is_rejected() -> None:
    policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    invalid = copy.deepcopy(policy)
    invalid["components"]["keystone"]["tempest_tests"] = ["["]

    with pytest.raises(
        PolicyError,
        match=r"components\.keystone\.tempest_tests\[0\] "
        r"is not a valid regular expression",
    ):
        Planner(invalid)


def test_malformed_verification_check_is_rejected() -> None:
    policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    invalid = copy.deepcopy(policy)
    invalid["verification_checks"]["secrets"] = [{"service": "key_manager"}]

    with pytest.raises(
        PolicyError,
        match=r"verification_checks\.secrets\[0\]\.type must be a string",
    ):
        Planner(invalid)


def test_every_declared_role_maps_to_its_component(
    planner: Planner,
) -> None:
    for component_name, policy in planner.components.items():
        for role in policy.get("roles", [component_name.replace("-", "_")]):
            plan = plan_path(planner, f"roles/{role}/tasks/main.yml")
            assert component_name in plan["targets"]


def test_every_declared_chart_and_patch_maps_to_its_component(
    planner: Planner,
) -> None:
    for component_name, policy in planner.components.items():
        for chart in policy.get("charts", [component_name]):
            for chart_root in ("charts", "charts/patches"):
                plan = plan_path(
                    planner,
                    f"{chart_root}/{chart}/templates/deployment.yaml",
                )
                assert component_name in plan["targets"]


def test_every_role_is_explicitly_classified(planner: Planner) -> None:
    repository = POLICY_PATH.parents[1]

    for role_path in (repository / "roles").iterdir():
        if not role_path.is_dir() or not (role_path / "tasks").exists():
            continue
        plan = plan_path(planner, f"roles/{role_path.name}/tasks/main.yml")
        assert not any(
            match["rule"] == "unclassified" for match in plan["matches"]
        ), role_path.name


def test_every_chart_and_patch_is_explicitly_classified(
    planner: Planner,
) -> None:
    repository = POLICY_PATH.parents[1]

    for chart_path in (repository / "charts").glob("*/Chart.yaml"):
        chart = chart_path.parent.name
        for path in (
            f"charts/{chart}/Chart.yaml",
            f"charts/patches/{chart}/0001-example.patch",
        ):
            plan = plan_path(planner, path)
            assert not any(
                match["rule"] == "unclassified" for match in plan["matches"]
            ), path


def test_every_sequential_aio_role_has_a_component(
    planner: Planner,
) -> None:
    configured_roles = {
        role
        for component_name, policy in planner.components.items()
        for role in policy.get("roles", [component_name.replace("-", "_")])
    }
    deployed_roles = set()
    for playbook_name in (
        "infrastructure.yml",
        "monitoring.yml",
        "openstack.yml",
    ):
        playbook = yaml.safe_load(
            (POLICY_PATH.parents[1] / "playbooks" / playbook_name).read_text(
                encoding="utf-8"
            )
        )
        for play in playbook:
            for role in play.get("roles", []):
                deployed_roles.add(role["role"] if isinstance(role, dict) else role)

    assert deployed_roles <= configured_roles


def test_selective_ci_uses_main_sequential_molecule_flow() -> None:
    repository = POLICY_PATH.parents[1]
    converge = (repository / "molecule" / "aio" / "converge.yml").read_text(
        encoding="utf-8"
    )
    openstack = (repository / "playbooks" / "openstack.yml").read_text(encoding="utf-8")
    runner = (
        repository / "test-playbooks" / "molecule" / "selective-run.yml"
    ).read_text(encoding="utf-8")
    tempest_tasks = (repository / "roles" / "tempest" / "tasks" / "main.yml").read_text(
        encoding="utf-8"
    )
    tempest_vars = (repository / "roles" / "tempest" / "vars" / "main.yml").read_text(
        encoding="utf-8"
    )
    policy = POLICY_PATH.read_text(encoding="utf-8")

    assert "vexxhost.atmosphere.ceph" in converge
    assert "vexxhost.atmosphere.kubernetes" in converge
    assert "vexxhost.atmosphere.openstack" in converge
    assert "CEPH_CONTAINER_IMAGE" in openstack
    assert "CEPH_CONTAINER_BINARY" in openstack
    assert "'molecule'," in runner
    assert "'test'," in runner
    assert "--regex" in tempest_vars
    assert r"\bsmoke\b" in tempest_vars
    assert "--include-list" not in tempest_vars
    assert "image_ref_alt" in tempest_tasks
    assert "flavor_ref_alt" in tempest_tasks
    assert "ATMOSPHERE_CI_VERIFICATION_CHECKS" in runner
    assert "openstack.cloud.resources" in (
        repository / "molecule" / "aio" / "verify.yml"
    ).read_text(encoding="utf-8")
    assert "go build" not in converge
    assert "./bin/atmosphere" not in runner
    assert "dependency_options" not in policy


def test_full_aio_jobs_have_timeout_headroom() -> None:
    repository = POLICY_PATH.parents[1]
    zuul_config = yaml.safe_load(
        (repository / ".zuul.yaml").read_text(encoding="utf-8")
    )
    jobs = {item["job"]["name"]: item["job"] for item in zuul_config if "job" in item}

    for job_name in (
        "atmosphere-molecule-aio-openvswitch-selective",
        "atmosphere-molecule-aio-ovn-selective",
    ):
        assert jobs[job_name]["timeout"] == 10800
        assert jobs[job_name]["vars"]["atmosphere_ci_molecule_timeout"] == 9000
        assert jobs[job_name]["vars"]["manila_helm_timeout"] == "10m0s"


def test_zuul_plan_uses_speculative_parent() -> None:
    repository = POLICY_PATH.parents[1]
    zuul_config = yaml.safe_load(
        (repository / ".zuul.yaml").read_text(encoding="utf-8")
    )
    project = next(item["project"] for item in zuul_config if "project" in item)

    assert project["vars"]["atmosphere_ci_plan_base"] == "HEAD^1"
    assert project["vars"]["atmosphere_ci_plan_head"] == "HEAD"


def test_scheduler_filters_match_policy(planner: Planner) -> None:
    repository = POLICY_PATH.parents[1]
    zuul_config = yaml.safe_load(
        (repository / ".zuul.yaml").read_text(encoding="utf-8")
    )
    configured = {
        job["name"]
        .removeprefix("atmosphere-molecule-")
        .removesuffix("-selective"): job["irrelevant-files"]
        for item in zuul_config
        if "job" in item
        for job in [item["job"]]
    }
    for item in zuul_config:
        if "job" in item:
            assert item["job"]["match-on-config-updates"] is False

    samples = {"new-runtime-area/config.yaml"}
    for rule in planner.rules:
        samples.update(
            pattern.replace("**", "example/file.yml")
            .replace("*", "example")
            .replace("?", "x")
            for pattern in rule["paths"]
        )
    for component_name, component in planner.components.items():
        samples.update(
            f"roles/{role}/tasks/main.yml"
            for role in component.get("roles", [component_name.replace("-", "_")])
        )
        for chart in component.get("charts", [component_name]):
            samples.add(f"charts/{chart}/Chart.yaml")
            samples.add(f"charts/patches/{chart}/0001-change.patch")
        samples.update(
            pattern.replace("**", "example/file.yml")
            .replace("*", "example")
            .replace("?", "x")
            for pattern in component.get("paths", [])
        )

    for changed_path in samples:
        plan = plan_path(planner, changed_path)
        expected = {
            job_name
            for job_name, decision in plan["job_decisions"].items()
            if decision["run"]
        }
        scheduled = {
            job_name
            for job_name, patterns in configured.items()
            if not any(re.match(pattern, changed_path) for pattern in patterns)
        }
        assert scheduled == expected, changed_path


def test_scheduler_filters_preserve_full_fallback(planner: Planner) -> None:
    filters = planner.scheduler_irrelevant_files()

    for patterns in filters.values():
        assert not any(
            re.match(pattern, "new-runtime-area/config.yaml") for pattern in patterns
        )


def test_scheduler_filters_select_only_glance_job(planner: Planner) -> None:
    filters = planner.scheduler_irrelevant_files()
    changed_path = "roles/glance/README.md"

    scheduled = {
        job_name
        for job_name, patterns in filters.items()
        if not any(re.match(pattern, changed_path) for pattern in patterns)
    }

    assert scheduled == {"aio-openvswitch"}


def test_text_output_is_compact_and_readable(planner: Planner) -> None:
    output = render_plan(plan_path(planner, "roles/manila/tasks/main.yml"))

    assert "Selective Molecule plan: selective" in output
    assert "RUN  aio-openvswitch" in output
    assert "SKIP aio-ovn" in output
    assert "components:" in output
    assert "API checks: shared_file_system/share" in output
