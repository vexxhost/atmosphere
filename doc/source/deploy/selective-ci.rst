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
verification profiles.

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

Zuul rollout
============

The AIO job initially runs the planner in shadow mode. It writes
``ci-plan.json`` and prints the explanation, while the existing complete
deployment still runs. This allows reviewers to compare proposed closures with
real build results before they control Molecule deployment and verification.
