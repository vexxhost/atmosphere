# Copyright (c) 2024 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

import json
import os
import tempfile
import shutil

import rjsonnet
import yaml


def import_callback(base, rel):
    """
    :param base: The directory containing the code that did the import.
    :param rel: The path imported by the code.
    """
    path = os.path.join(base, rel)
    with open(path, "r") as f:
        return path, f.read()


def main():
    compiled_string = rjsonnet.evaluate_file(
        "roles/kube_prometheus_stack/files/jsonnet/rules.jsonnet",
        import_callback=import_callback,
    )
    compiled = json.loads(compiled_string)

    tempdir = tempfile.mkdtemp()
    rule_files = []

    try:
        for rule_file, data in compiled.items():
            file_name = rule_file + ".yml"
            path = os.path.join(tempdir, file_name)

            if os.path.exists(path):
                raise Exception(f"File {path} already exists")
            with open(path, "w") as f:
                yaml.dump(data, f)

            rule_files.append(path)

        with open("roles/kube_prometheus_stack/files/jsonnet/tests.yml") as f:
            tests = yaml.safe_load(f)

        tests["rule_files"] = rule_files

        tests_file = os.path.join(tempdir, "tests.yml")
        with open(tests_file, "w") as f:
            yaml.dump(tests, f)

        # TODO(mnaser): Enable JUnit output
        os.system(f"promtool test rules {tests_file}")
    finally:
        shutil.rmtree(tempdir)


if __name__ == "__main__":
    main()
