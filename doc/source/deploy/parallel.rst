================================
Parallel deployment orchestrator
================================

Atmosphere ships a Go binary, ``atmosphere``, that deploys components in
parallel waves based on a directed acyclic graph (DAG) of dependencies.
Components without a direct dependency on each other run concurrently,
which shortens full deployment time compared to the sequential
role-by-role flow driven by ``site.yml``.

The orchestrator is additive. It doesn't change Ansible roles,
variables, or playbooks. Existing ``ansible-playbook site.yml`` flows
continue to work unchanged.

Building the binary
===================

Build the binary from the repository root:

.. code-block:: console

  $ CGO_ENABLED=0 go build -o ./bin/atmosphere ./cmd/atmosphere

The resulting binary lives at ``./bin/atmosphere``. Copy it onto
``PATH`` if you'd like to run it from any directory.

Running a deployment
====================

The ``deploy`` command takes an inventory path and an optional list of
component tags:

.. code-block:: console

  $ atmosphere deploy --inventory ./inventory.yaml

The command requires the same Ansible runtime that ``site.yml`` needs.
Activate the project virtual environment, or otherwise make
``ansible-playbook`` and the ``vexxhost.atmosphere`` collection
available on ``PATH``, before invoking ``atmosphere deploy``.

Operating modes
===============

The orchestrator supports three modes, chosen by how you pass
``--tags``:

Full deployment
  Without ``--tags``, the orchestrator runs every component across
  parallel waves derived from the dependency graph. Components in
  the same wave run concurrently; later waves start once their
  prerequisites finish.

Single tag
  With one tag, for example ``--tags keystone``, the orchestrator
  delegates to ``ansible-playbook site.yml --tags keystone``. The
  behavior matches the existing tag-based flow.

Multiple tags
  With several comma-separated tags, for example
  ``--tags nova,keystone``, the orchestrator builds a subgraph that
  contains the requested components plus their transitive
  dependencies, then runs them in parallel waves.

Concurrency control
===================

Use ``--concurrency`` to cap the number of components that run at the
same time inside a wave:

.. code-block:: console

  $ atmosphere deploy --inventory ./inventory.yaml --concurrency 4

The default, ``0``, lets every component in a wave run concurrently.
Lower values reduce peak load on the deploy host and target nodes at
the cost of longer wave durations.

Output
======

Output from each component streams to standard output with a
``[component-name]`` prefix so that you can tell concurrent log lines
apart. A non-zero exit from any component cancels the remaining work
in the current wave and surfaces the failure.
