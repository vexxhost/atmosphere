===============================
Selective Molecule CI planning
===============================

Atmosphere can map pull request changes to a smaller Molecule deployment.
The planner keeps change impact separate from deployment dependencies:

* Changed paths select direct test targets.
* Functional test requirements add any extra test targets.
* The deployment graph expands those roots into the components required by a
  fresh environment.
* Verification profiles describe the focused checks that should run.

The policy lives in ``ci/molecule-plan.yaml``. The Go deployment registry
supplies component role and chart paths. The policy contains additional paths,
shared-code rules, functional test requirements, backend selection, and
verification profiles. It also maps the static Zuul jobs to the variants or
verification profiles they can execute.

Creating a plan
===============

Build the ``atmosphere`` binary, then pass changed paths directly:

.. code-block:: console

  $ atmosphere ci plan \
      --changed-file roles/manila/tasks/main.yml

The planner also accepts ``git diff --name-status`` records:

.. code-block:: console

  $ git diff --name-status --find-renames origin/main...HEAD |
      atmosphere ci plan --files-from -

Or let the planner collect the Git diff:

.. code-block:: console

  $ atmosphere ci plan --base origin/main --head HEAD

Use JSON when another CI step will consume the plan:

.. code-block:: console

  $ atmosphere ci plan \
      --base origin/main \
      --head HEAD \
      --format json \
      --output ci-plan.json

Plan modes
==========

``noop``
  Every changed path matches an explicit Molecule ignore rule.

``selective``
  The plan contains direct targets, deployment roots, verification profiles,
  and one component closure for each required network backend.

``full``
  The plan requires both complete network-backend variants.

The policy fails safely. Unknown runtime paths, shared deployment code, CI
policy changes, and planner changes select ``full`` rather than silently
omitting tests. Renames and copies evaluate both the old and new paths.
Failure to generate or read a plan in Zuul also runs every Molecule job with
its complete deployment.

Job selection
=============

Zuul still declares every Molecule job statically so that its configuration is
easy to inspect. At runtime each job reads its decision from ``ci-plan.json``:

* An AIO job runs only when the plan contains its network backend.
* Dedicated CSI and Keycloak jobs run only when their verification profile is
  requested.
* A documentation-only plan skips every Molecule scenario.
* A complete fallback runs every job.

The ``jobs`` mapping controls this behavior:

.. code-block:: yaml

  jobs:
    aio-openvswitch:
      scenario: aio
      network_backend: openvswitch
      skip_if_only_verification_profiles:
        - csi
        - keycloak-federation

    keycloak:
      scenario: keycloak
      verification_profiles:
        - keycloak-federation

For a selective AIO job, the deployment variant becomes the comma-separated
``atmosphere deploy --tags`` list. Tempest receives the same component list and
marks services that were not deployed as unavailable. This keeps focused
verification from querying unrelated services.

The deployment runs directly as a Zuul ``command`` task rather than as a
nested Molecule Ansible process. This makes the deployment's Ansible output
visible in the live Zuul console. The same deployment is run a second time to
retain the idempotence check before Molecule verification.

Selection examples
==================

The current policy produces these representative job decisions:

``roles/keystone/**``
  Run the Open vSwitch AIO closure and the dedicated Keycloak federation job.
  Skip OVN and both CSI jobs.

``roles/manila/**``
  Run only the Open vSwitch AIO closure, including Manila's storage, image,
  compute, placement, and network test requirements.

``roles/magnum/**``
  Run only the Open vSwitch AIO job with Magnum's broader orchestration,
  secrets, storage, compute, network, and load-balancing environment.

``roles/neutron/**``
  Run both AIO network variants.

``roles/ceph_csi_rbd/**``
  Run the two dedicated CSI scenarios and skip both AIO jobs.

Extending the policy
====================

Add service-specific behavior under ``components``. For example:

.. code-block:: yaml

  components:
    manila:
      verification_profiles:
        - shared-file-system
      network_backends:
        - canonical

``test_requires`` contains services needed by functional verification but not
by normal deployment ordering. Magnum uses this to request the broader compute,
network, orchestration, secrets, storage, and load-balancing environment.

Use a rule for paths which affect several components or which must force the
full fallback:

.. code-block:: yaml

  rules:
    - name: shared-deployment-code
      action: full
      paths:
        - roles/openstack_helm_endpoints/**

Run the Go tests after every policy change. Configuration validation rejects
unknown components, invalid actions, unsupported globs, and invalid backend
references.

Validate the policy directly with:

.. code-block:: console

  $ atmosphere ci validate

Zuul execution
==============

The pre-run playbook writes ``ci-plan.json`` into the build logs and prints the
human-readable explanation. Every job then reports its run or skip decision,
reason, component closure, and verification profiles before doing any
deployment work.
