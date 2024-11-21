# Copyright (c) 2024 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import subprocess
import glob

def run_helm_unittest(charts_dir, exclusions):
    """
    :param charts_dir: The directory containing Helm charts.
    :param exclusions: List of subdirectories to exclude.
    """
    all_tests_passed = True
    charts = [
        os.path.basename(d)
        for d in glob.glob(os.path.join(charts_dir, "*"))
        if os.path.isdir(d) and os.path.basename(d) not in exclusions
    ]
    for chart in charts:
        print(f"Running helm unittest for chart: {chart}")
        chart_tests_path = f"../../roles/{chart}/tests/*.yaml"
        chart_path = os.path.join(charts_dir, chart)
        try:
            # Run helm unittest
            subprocess.run(
                ["helm", "unittest", "-f", chart_tests_path, chart_path],
                check=True,
            )
            print(f"Helm unitest  passed for chart: {chart}")
        except subprocess.CalledProcessError as e:
            print(f"Helm unittest failed for chart: {chart}")
            all_tests_passed = False
            raise e
    if all_tests_passed:
        print("\nAll Helm unitests passed successfully!")
        exit(0)
    else:
        print("\nOne or more charts had test failures.")
        exit(1)

def main():
    charts_dir = os.getenv("CHARTS_DIR", "charts")
    exclusions = ["patches"]
    run_helm_unittest(charts_dir, exclusions)

if __name__ == "__main__":
    main()
