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

import click
from oslo_log import log as logging  # type: ignore

from atmosphere import exceptions, workflows

LOG = logging.getLogger(__name__)


@click.command()
@click.option("-i", "--inventory", type=click.Path(exists=True), required=True)
@click.option("-l", "--limit", multiple=True)
@click.option("-t", "--tags", multiple=True)
def command(inventory, tags, limit):
    LOG.info("Deploying")

    try:
        workflows.deploy(inventory, tags, limit)
    except exceptions.AnsiblePlaybookError:
        LOG.error("Failed to deploy")
        raise click.Abort()
