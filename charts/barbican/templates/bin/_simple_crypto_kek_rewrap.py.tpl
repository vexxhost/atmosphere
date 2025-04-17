#!/usr/bin/env python

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import argparse
import base64
import sys

from cryptography import fernet
from oslo_db.sqlalchemy import session
from sqlalchemy import orm
from sqlalchemy.orm import scoping

from barbican.common import utils
from barbican.model import models
from barbican.plugin.crypto import simple_crypto

# Use config values from simple_crypto
CONF = simple_crypto.CONF


class KekRewrap(object):

    def __init__(self, conf, old_keks):
        self.dry_run = False
        self.db_engine = session.create_engine(conf.database.connection)
        self._session_creator = scoping.scoped_session(
            orm.sessionmaker(
                bind=self.db_engine,
            )
        )
        self.crypto_plugin = simple_crypto.SimpleCryptoPlugin(conf)
        self.plugin_name = utils.generate_fullname_for(self.crypto_plugin)

        if hasattr(self.crypto_plugin, 'master_kek'):
            self.encryptor = fernet.Fernet(self.crypto_plugin.master_kek)
        else:
            self.encryptor = fernet.MultiFernet(
                [fernet.Fernet(x) for x in self.crypto_plugin.master_keys]
            )
        self.decryptor = fernet.MultiFernet(
            [fernet.Fernet(x.encode('utf-8')) for x in old_keks]
        )

    def rewrap_kek(self, project, kek):
        with self.db_session.begin():
            plugin_meta = kek.plugin_meta

            # try to unwrap with the target kek, and if successful, skip
            try:
                if self.encryptor.decrypt(plugin_meta.encode('utf-8')):
                    print('Project KEK {} is already wrapped with target KEK, skipping'.format(kek.id))
                    return
            except fernet.InvalidToken:
                pass

            # decrypt with the old kek
            print('Unwrapping Project KEK {}'.format(kek.id))
            try:
                decrypted_plugin_meta = self.decryptor.decrypt(plugin_meta.encode('utf-8'))
            except fernet.InvalidToken:
                print('Failed to unwrap Project KEK {}'.format(kek.id))
                raise

            # encrypt with the new kek
            print('Rewrapping Project KEK {}'.format(kek.id))
            try:
                new_plugin_meta = self.encryptor.encrypt(decrypted_plugin_meta).decode('utf-8')
            except fernet.InvalidToken:
                print('Failed to wrap Project KEK {}'.format(kek.id))
                raise

            if self.dry_run:
                return

            # Update KEK metadata in DB
            print('Storing updated Project KEK {}'.format(kek.id))
            kek.plugin_meta = new_plugin_meta

    def get_keks_for_project(self, project):
        keks = []

        if self.db_session.in_transaction():
            keks = self.db_session.query(models.ProjectSecretStore).filter(
                models.ProjectSecretStore.project_id == project.id).all()
        else:
            with self.db_session.begin() as transaction:
                keks = self.db_session.query(models.ProjectSecretStore).filter(
                    models.ProjectSecretStore.project_id == project.id).all()
        return keks

    def get_projects(self):
        print('Retrieving all available projects')

        projects = []
        with self.db_session.begin() as transaction:
            projects = transaction.session.query(models.Project).all()

        return projects

    @property
    def db_session(self):
        return self._session_creator()

    def execute(self, dry_run=True):
        self.dry_run = dry_run
        if self.dry_run:
            print('-- Running in dry-run mode --')

        projects = self.get_projects()
        successes = []
        failures = []

        for project in projects:
            keks = self.get_keks_for_project(project)
            for kek in keks:
                try:
                    self.rewrap_kek(project, kek)
                    successes.append(kek.id)
                except Exception:
                    failures.append(kek.id)

        if successes:
            print('Sucessfully processed the following KEKs:')
            print('\n'.join(successes))

        if failures:
            print('Failed to rewrap the following KEKs:')
            print('\n'.join(failures))
            sys.exit(1)


def main():
    script_desc = 'Utility to re-wrap Project KEKs after rotating the global KEK.'

    parser = argparse.ArgumentParser(description=script_desc)
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Displays changes that will be made (Non-destructive)'
    )
    parser.add_argument(
        '--old-keks',
        default="dGhpcnR5X3R3b19ieXRlX2tleWJsYWhibGFoYmxhaGg=",
        help='Old key encryption keys previously used by Simple Crypto Plugin. '
             'A comma separated string of list contain keys '
             '( with formate 32 bytes and base64-encoded ). '
             'First key in list is used for ecnrypting new data. '
             'Additional keys used for decrypting existing data.'
    )
    args = parser.parse_args()

    rewrapper = KekRewrap(CONF, args.old_keks.split(","))
    rewrapper.execute(args.dry_run)


if __name__ == '__main__':
    main()
