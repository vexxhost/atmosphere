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

import subprocess
from pathlib import Path

import click
from oslo_log import log as logging  # type: ignore

from atmosphere import exceptions, workflows

LOG = logging.getLogger(__name__)


@click.group()
def group():
    pass


def validate_molecule_scenario(ctx, param, value):
    molecule_yml = Path("molecule") / value / "molecule.yml"
    if not molecule_yml.exists():
        raise click.BadParameter("Scenario does not exist: %s" % value)
    return value


@group.command()
@click.option("-s", "--scenario", callback=validate_molecule_scenario, required=True)
def converge(scenario):
    subprocess.run(["molecule", "create", "-s", scenario])
    inventory_path = (
        Path.home() / ".cache" / "molecule" / Path.cwd().stem / scenario / "inventory"
    )

    try:
        workflows.deploy(inventory=inventory_path)
    except exceptions.AnsiblePlaybookError:
        LOG.error("Failed to converge")
        raise click.Abort()
